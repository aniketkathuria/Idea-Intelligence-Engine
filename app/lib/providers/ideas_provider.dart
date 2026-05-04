import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/idea.dart';
import '../models/cluster.dart';
import '../database/db_helper.dart';
import '../services/api_service.dart';

class IdeasProvider extends ChangeNotifier {
  final _db  = DbHelper();
  final _api = ApiService();

  List<Idea>    _ideas    = [];
  List<Cluster> _clusters = [];
  bool _loading = false;

  List<Idea>    get ideas    => _ideas;
  List<Cluster> get clusters => _clusters;
  bool          get loading  => _loading;

  String get apiService => _api.toString();

  // ── Boot ─────────────────────────────────────────────

  Future<void> load() async {
    _ideas    = await _db.loadAllIdeas();
    _clusters = await _db.loadAllClusters();
    notifyListeners();
    // Resume polling for any ideas that were mid-analysis when app was killed
    _resumeStuckIdeas();
  }

  // ── Create / update note ──────────────────────────────

  Future<Idea> createIdea(String rawIdea) async {
    final now  = DateTime.now();
    final idea = Idea(rawIdea: rawIdea, createdAt: now, updatedAt: now);
    final id   = await _db.insertIdea(idea);
    final saved = idea.copyWith(id: id);
    _ideas.insert(0, saved);
    notifyListeners();
    return saved;
  }

  Future<void> saveNote(Idea idea) async {
    final updated = idea.copyWith(updatedAt: DateTime.now());
    await _db.updateIdea(updated);
    _replace(updated);
    notifyListeners();
  }

  Future<void> deleteIdea(int id) async {
    await _db.deleteIdea(id);
    _ideas.removeWhere((i) => i.id == id);
    notifyListeners();
  }

  // ── Analyze ───────────────────────────────────────────

  Future<void> analyzeIdea(
    Idea idea, {
    String depth = 'balanced',
    void Function(String stage)? onStage,
  }) async {
    final processing = idea.copyWith(status: 'processing', updatedAt: DateTime.now());
    await _db.updateIdea(processing);
    _replace(processing);
    notifyListeners();

    try {
      try { onStage?.call('Sending to engine…'); } catch (_) {}

      // Submit job — store job_id immediately so we can resume if app is killed
      final jobId = await _api.submitIdea(
        rawIdea:   idea.rawIdea,
        pastIdeas: _ideas.where((i) => i.id != idea.id && i.embedding != null).toList(),
        depth:     depth,
      );
      await _saveJobId(idea.id!, jobId);

      try { onStage?.call('Processing…'); } catch (_) {}

      final result = await _api.pollJob(jobId);
      await _clearJobId(idea.id!);

      try { onStage?.call('Saving result…'); } catch (_) {}

      await _saveResult(idea, result);
    } catch (e) {
      await _clearJobId(idea.id!);
      final failed = idea.copyWith(status: 'failed', updatedAt: DateTime.now());
      await _db.updateIdea(failed);
      _replace(failed);
      notifyListeners();
      rethrow;
    }
  }

  // ── Resume stuck ideas on app open ───────────────────

  void _resumeStuckIdeas() {
    final stuck = _ideas.where((i) => i.status == 'processing').toList();
    for (final idea in stuck) {
      _tryResume(idea);
    }
  }

  Future<void> _tryResume(Idea idea) async {
    final jobId = await _loadJobId(idea.id!);

    if (jobId != null) {
      try {
        final result = await _api.pollJob(jobId);
        await _clearJobId(idea.id!);
        await _saveResult(idea, result);
        return;
      } on ApiException catch (e) {
        await _clearJobId(idea.id!);
        // Job expired means Render restarted and lost the job — re-submit below
        if (!e.message.contains('expired')) {
          final failed = idea.copyWith(status: 'failed', updatedAt: DateTime.now());
          await _db.updateIdea(failed);
          _replace(failed);
          notifyListeners();
          return;
        }
      }
    }

    // No job_id stored, or job expired on server — re-submit automatically.
    // The user already intended to process this idea; we honour that silently.
    try {
      final newJobId = await _api.submitIdea(
        rawIdea:   idea.rawIdea,
        pastIdeas: _ideas.where((i) => i.id != idea.id && i.embedding != null).toList(),
      );
      await _saveJobId(idea.id!, newJobId);
      final result = await _api.pollJob(newJobId);
      await _clearJobId(idea.id!);
      await _saveResult(idea, result);
    } catch (_) {
      await _clearJobId(idea.id!);
      final failed = idea.copyWith(status: 'failed', updatedAt: DateTime.now());
      await _db.updateIdea(failed);
      _replace(failed);
      notifyListeners();
    }
  }

  // ── Save analysis result (shared by analyzeIdea + _tryResume) ──

  Future<void> _saveResult(Idea idea, Map<String, dynamic> result) async {
    final evaluation = result['evaluation']     as Map<String, dynamic>?;
    final research   = result['research']       as List<dynamic>?;
    final rawEmbed   = result['embedding']      as List<dynamic>?;
    final embedding  = rawEmbed?.map((e) => (e as num).toDouble()).toList();
    final synthesis  = result['synthesis']      as Map<String, dynamic>?;
    final action     = result['cluster_action'] as String? ?? 'none';
    final matchedIds = List<int>.from((result['matched_idea_ids'] as List? ?? []));

    final completed = idea.copyWith(
      status:     'completed',
      category:   evaluation?['category'] as String?,
      evaluation: evaluation,
      research:   research,
      embedding:  embedding,
      synthesis:  synthesis,
      updatedAt:  DateTime.now(),
    );
    await _db.updateIdea(completed);
    _replace(completed);

    await _applyCluster(
      newIdea:    completed,
      action:     action,
      serverId:   result['cluster_id'] as int?,
      matchedIds: matchedIds,
      synthesis:  synthesis,
    );

    notifyListeners();
  }

  // ── Job ID persistence (SharedPreferences) ────────────

  Future<void> _saveJobId(int ideaId, String jobId) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('job_$ideaId', jobId);
  }

  Future<String?> _loadJobId(int ideaId) async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('job_$ideaId');
  }

  Future<void> _clearJobId(int ideaId) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('job_$ideaId');
  }

  // ── Cluster logic (applied client-side) ──────────────

  Future<void> _applyCluster({
    required Idea   newIdea,
    required String action,
    required int?   serverId,
    required List<int> matchedIds,
    Map<String, dynamic>? synthesis,
  }) async {
    if (action == 'none' || synthesis == null) return;
    if (!(synthesis['should_merge'] as bool? ?? false)) return;

    if (action == 'expand' && serverId != null) {
      final existing = _clusters.firstWhere(
        (c) => c.id == serverId,
        orElse: () => Cluster(id: serverId, ideaIds: [], createdAt: DateTime.now()),
      );
      final updatedIds = {...existing.ideaIds, newIdea.id!}.toList();
      final updated = existing.copyWith(
        superIdea:      (synthesis['super_idea'] ?? synthesis['merged_super_idea_summary']) as String?,
        mergeReasoning: synthesis['merge_reasoning'] as String?,
        ideaIds:        updatedIds,
      );
      if (_clusters.any((c) => c.id == serverId)) {
        await _db.updateCluster(updated);
        _clusters = _clusters.map((c) => c.id == serverId ? updated : c).toList();
      } else {
        final newId = await _db.insertCluster(updated);
        _clusters.insert(0, updated.copyWith(id: newId));
      }
      final withCluster = newIdea.copyWith(clusterId: serverId);
      await _db.updateIdea(withCluster);
      _replace(withCluster);

    } else if (action == 'create') {
      final allIds = {...matchedIds, newIdea.id!}.toList();
      final cluster = Cluster(
        superIdea:      (synthesis['super_idea'] ?? synthesis['merged_super_idea_summary']) as String?,
        mergeReasoning: synthesis['merge_reasoning'] as String?,
        ideaIds:        allIds,
        createdAt:      DateTime.now(),
      );
      final clusterId = await _db.insertCluster(cluster);
      final saved     = cluster.copyWith(id: clusterId);
      _clusters.insert(0, saved);

      for (final id in allIds) {
        final target  = _ideas.firstWhere((i) => i.id == id, orElse: () => newIdea);
        final updated = target.copyWith(clusterId: clusterId);
        await _db.updateIdea(updated);
        _replace(updated);
      }
    }
  }

  // ── Helpers ───────────────────────────────────────────

  void _replace(Idea updated) {
    _ideas = _ideas.map((i) => i.id == updated.id ? updated : i).toList();
  }

  Cluster? clusterFor(Idea idea) {
    if (idea.clusterId == null) return null;
    try { return _clusters.firstWhere((c) => c.id == idea.clusterId); }
    catch (_) { return null; }
  }

  List<Idea> ideasInCluster(Cluster cluster) =>
      _ideas.where((i) => cluster.ideaIds.contains(i.id)).toList();

  Future<String> getBackendUrl() => _api.baseUrl;
  Future<void>   setBackendUrl(String url) => _api.setBaseUrl(url);
  Future<bool>   pingBackend() => _api.ping();
}
