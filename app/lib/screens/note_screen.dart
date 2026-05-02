import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/ideas_provider.dart';
import '../models/idea.dart';
import '../theme/app_theme.dart';
import '../widgets/evaluator_view.dart';
import '../widgets/synthesis_view.dart';

class NoteScreen extends StatefulWidget {
  final Idea idea;
  final bool isNew;
  const NoteScreen({super.key, required this.idea, this.isNew = false});

  @override State<NoteScreen> createState() => _NoteScreenState();
}

class _NoteScreenState extends State<NoteScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabs;
  late TextEditingController _textCtrl;
  late Idea _current;

  String _analyzeStage = '';
  bool   _analyzing    = false;
  String _depth        = 'balanced';

  @override
  void initState() {
    super.initState();
    _current  = widget.idea;
    _tabs     = TabController(length: 3, vsync: this);
    _textCtrl = TextEditingController(text: widget.idea.rawIdea);
    _textCtrl.addListener(_onTextChanged);
  }

  @override
  void dispose() {
    _textCtrl.removeListener(_onTextChanged);
    _textCtrl.dispose();
    _tabs.dispose();
    super.dispose();
  }

  void _onTextChanged() {
    // Debounce save is handled in _saveNote
  }

  Future<void> _saveNote() async {
    final text = _textCtrl.text;
    if (text == _current.rawIdea) return;
    final updated = _current.copyWith(rawIdea: text);
    await context.read<IdeasProvider>().saveNote(updated);
    if (mounted) setState(() => _current = updated);
  }

  Future<void> _analyze() async {
    final text = _textCtrl.text.trim();
    if (text.isEmpty) {
      _showSnack('Write something first.');
      return;
    }

    await _saveNote();

    setState(() { _analyzing = true; _analyzeStage = 'Starting…'; });
    _tabs.animateTo(1); // jump to Evaluator tab

    try {
      await context.read<IdeasProvider>().analyzeIdea(
        _current.copyWith(rawIdea: text),
        depth: _depth,
        onStage: (s) => setState(() => _analyzeStage = s),
      );
      // Reload updated idea from provider
      final updated = context.read<IdeasProvider>()
          .ideas.firstWhere((i) => i.id == _current.id, orElse: () => _current);
      if (mounted) setState(() { _current = updated; _analyzing = false; });
    } catch (e) {
      if (mounted) {
        setState(() => _analyzing = false);
        _showSnack('Analysis failed: $e');
        _tabs.animateTo(0);
      }
    }
  }

  void _showSnack(String msg) => ScaffoldMessenger.of(context)
      .showSnackBar(SnackBar(
        content: Text(msg),
        backgroundColor: AppColors.surface2,
        behavior: SnackBarBehavior.floating,
      ));

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<IdeasProvider>();
    // Keep _current in sync with provider
    final live = provider.ideas.firstWhere(
      (i) => i.id == _current.id, orElse: () => _current);
    if (live.status != _current.status || live.evaluation != _current.evaluation) {
      _current = live;
    }

    final cluster     = provider.clusterFor(_current);
    final clusterIdeas = cluster != null ? provider.ideasInCluster(cluster) : <Idea>[];

    return PopScope(
      onPopInvokedWithResult: (_, __) => _saveNote(),
      child: Scaffold(
        backgroundColor: AppColors.bg,
        appBar: AppBar(
          backgroundColor: AppColors.bg,
          leading: IconButton(
            icon: const Icon(Icons.arrow_back_ios_new, size: 18, color: AppColors.textMuted),
            onPressed: () async { await _saveNote(); Navigator.pop(context); },
          ),
          title: Text(
            _current.title.isEmpty ? 'New Note' : _current.title,
            style: const TextStyle(color: AppColors.textMuted, fontSize: 14),
            overflow: TextOverflow.ellipsis,
          ),
          bottom: TabBar(
            controller: _tabs,
            tabs: const [
              Tab(text: 'Note'),
              Tab(text: 'Evaluator'),
              Tab(text: 'Synthesis'),
            ],
          ),
        ),
        body: TabBarView(
          controller: _tabs,
          physics: _analyzing
              ? const NeverScrollableScrollPhysics()
              : const AlwaysScrollableScrollPhysics(),
          children: [
            _NoteTab(
              ctrl:      _textCtrl,
              current:   _current,
              analyzing: _analyzing,
              stage:     _analyzeStage,
              depth:     _depth,
              onDepthChanged: (d) => setState(() => _depth = d),
              onAnalyze: _analyze,
            ),
            _analyzing
                ? _AnalyzingView(stage: _analyzeStage)
                : EvaluatorView(idea: _current),
            SynthesisView(
              idea:         _current,
              cluster:      cluster,
              clusterIdeas: clusterIdeas,
            ),
          ],
        ),
      ),
    );
  }
}

// ── Note tab ─────────────────────────────────────────────────

class _NoteTab extends StatelessWidget {
  final TextEditingController ctrl;
  final Idea    current;
  final bool    analyzing;
  final String  stage;
  final String  depth;
  final ValueChanged<String> onDepthChanged;
  final VoidCallback onAnalyze;

  const _NoteTab({
    required this.ctrl,
    required this.current,
    required this.analyzing,
    required this.stage,
    required this.depth,
    required this.onDepthChanged,
    required this.onAnalyze,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Expanded(
          child: TextField(
            controller: ctrl,
            maxLines: null,
            expands: true,
            autofocus: current.rawIdea.isEmpty,
            style: const TextStyle(
              color: AppColors.text,
              fontSize: 15,
              height: 1.7,
            ),
            decoration: const InputDecoration(
              contentPadding: EdgeInsets.fromLTRB(20, 20, 20, 0),
              hintText: 'Write your idea, thought, or observation…',
              border: InputBorder.none,
            ),
            keyboardType: TextInputType.multiline,
            textCapitalization: TextCapitalization.sentences,
          ),
        ),
        _BottomBar(
          current:        current,
          analyzing:      analyzing,
          stage:          stage,
          depth:          depth,
          onDepthChanged: onDepthChanged,
          onAnalyze:      onAnalyze,
        ),
      ],
    );
  }
}

class _BottomBar extends StatelessWidget {
  final Idea    current;
  final bool    analyzing;
  final String  stage;
  final String  depth;
  final ValueChanged<String> onDepthChanged;
  final VoidCallback onAnalyze;

  const _BottomBar({
    required this.current,
    required this.analyzing,
    required this.stage,
    required this.depth,
    required this.onDepthChanged,
    required this.onAnalyze,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 10, 16, 20),
      decoration: const BoxDecoration(
        color: AppColors.surface,
        border: Border(top: BorderSide(color: AppColors.border, width: 0.5)),
      ),
      child: Row(
        children: [
          // Depth selector
          _DepthChip(
            label: 'Fast',
            selected: depth == 'fast',
            onTap: () => onDepthChanged('fast'),
          ),
          const SizedBox(width: 6),
          _DepthChip(
            label: 'Balanced',
            selected: depth == 'balanced',
            onTap: () => onDepthChanged('balanced'),
          ),
          const SizedBox(width: 6),
          _DepthChip(
            label: 'Deep',
            selected: depth == 'deep',
            onTap: () => onDepthChanged('deep'),
          ),
          const Spacer(),
          // Analyze button
          GestureDetector(
            onTap: analyzing ? null : onAnalyze,
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 9),
              decoration: BoxDecoration(
                color: analyzing ? AppColors.surface2 : AppColors.amber,
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (analyzing) ...[
                    const SizedBox(
                      width: 12, height: 12,
                      child: CircularProgressIndicator(
                        strokeWidth: 1.5,
                        color: AppColors.amber,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      stage.isNotEmpty ? stage : 'Analyzing…',
                      style: const TextStyle(
                        color: AppColors.amber, fontSize: 12,
                      ),
                    ),
                  ] else ...[
                    const Icon(Icons.auto_awesome, size: 14, color: AppColors.bg),
                    const SizedBox(width: 6),
                    Text(
                      current.isAnalyzed ? 'Re-analyze' : 'Analyze',
                      style: const TextStyle(
                        color: AppColors.bg, fontSize: 13,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _DepthChip extends StatelessWidget {
  final String   label;
  final bool     selected;
  final VoidCallback onTap;
  const _DepthChip({required this.label, required this.selected, required this.onTap});

  @override Widget build(BuildContext context) => GestureDetector(
    onTap: onTap,
    child: Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color:  selected ? AppColors.amberDim : Colors.transparent,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: selected ? AppColors.amber : AppColors.border,
          width: 0.5,
        ),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: selected ? AppColors.amber : AppColors.textDim,
          fontSize: 11,
          fontWeight: selected ? FontWeight.w600 : FontWeight.w400,
        ),
      ),
    ),
  );
}

class _AnalyzingView extends StatelessWidget {
  final String stage;
  const _AnalyzingView({required this.stage});

  @override Widget build(BuildContext context) => Center(
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        const SizedBox(
          width: 40, height: 40,
          child: CircularProgressIndicator(color: AppColors.amber, strokeWidth: 2),
        ),
        const SizedBox(height: 24),
        Text(
          stage.isNotEmpty ? stage : 'Analyzing…',
          style: const TextStyle(color: AppColors.textMuted, fontSize: 14),
        ),
        const SizedBox(height: 8),
        const Text(
          'This may take 1–3 minutes',
          style: TextStyle(color: AppColors.textDim, fontSize: 12),
        ),
      ],
    ),
  );
}
