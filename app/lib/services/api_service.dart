import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/idea.dart';

class ApiException implements Exception {
  final String message;
  final int?   statusCode;
  ApiException(this.message, {this.statusCode});
  @override String toString() => message;
}

class ApiService {
  static const _defaultUrl = 'https://idea-engine-zbno.onrender.com';
  static const _prefKey    = 'backend_url';

  Future<String> get baseUrl async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_prefKey) ?? _defaultUrl;
  }

  Future<void> setBaseUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_prefKey, url.trimRight().replaceAll(RegExp(r'/$'), ''));
  }

  /// Step 1: Submit idea — returns job_id immediately.
  Future<String> submitIdea({
    required String rawIdea,
    required List<Idea> pastIdeas,
    String depth    = 'balanced',
    String? category,
  }) async {
    final url  = await baseUrl;
    final body = jsonEncode({
      'raw_idea':   rawIdea,
      'past_ideas': pastIdeas.map((i) => i.toApiShape()).toList(),
      'depth':      depth,
      if (category != null) 'category': category,
    });

    final res = await http.post(
      Uri.parse('$url/process-idea'),
      headers: {'Content-Type': 'application/json'},
      body: body,
    ).timeout(
      const Duration(seconds: 30),
      onTimeout: () => throw ApiException('Submit timed out'),
    );

    if (res.statusCode != 200) {
      String detail = 'Server error ${res.statusCode}';
      try { detail = jsonDecode(res.body)['detail'] ?? detail; } catch (_) {}
      throw ApiException(detail, statusCode: res.statusCode);
    }

    return jsonDecode(res.body)['job_id'] as String;
  }

  /// Step 2: Poll until job completes. Safe to call after app resume.
  /// Individual poll failures are swallowed — only hard errors (job failed,
  /// job not found, 10-min deadline) stop the loop.
  Future<Map<String, dynamic>> pollJob(String jobId) async {
    final url      = await baseUrl;
    final deadline = DateTime.now().add(const Duration(minutes: 10));

    while (DateTime.now().isBefore(deadline)) {
      await Future.delayed(const Duration(seconds: 5));

      try {
        final res = await http.get(
          Uri.parse('$url/idea-status/$jobId'),
        ).timeout(const Duration(seconds: 15));

        if (res.statusCode == 200) {
          final data = Map<String, dynamic>.from(jsonDecode(res.body));
          if (data['status'] == 'completed') return data;
          if (data['status'] == 'failed') {
            throw ApiException(data['error'] as String? ?? 'Processing failed');
          }
          // status == 'processing' — keep polling
        } else if (res.statusCode == 404) {
          // Job expired (server restarted) — no point continuing
          throw ApiException('Job expired on server');
        }
        // Any other HTTP error: swallow and retry next tick
      } on ApiException {
        rethrow; // only hard errors bubble up
      } catch (_) {
        // Network error on this poll (background restriction, brief disconnect)
        // Swallow and try again in 5 seconds
      }
    }

    throw ApiException('Processing timed out after 10 minutes');
  }

  /// Health check — returns true if backend is reachable.
  Future<bool> ping() async {
    try {
      final url = await baseUrl;
      final res = await http.get(Uri.parse('$url/')).timeout(const Duration(seconds: 10));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }
}
