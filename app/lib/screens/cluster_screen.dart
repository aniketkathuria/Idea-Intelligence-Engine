import 'package:flutter/material.dart';
import '../models/cluster.dart';
import '../models/idea.dart';
import '../theme/app_theme.dart';
import 'note_screen.dart';

class ClusterScreen extends StatelessWidget {
  final Cluster    cluster;
  final List<Idea> ideas;

  const ClusterScreen({super.key, required this.cluster, required this.ideas});

  // Find the richest synthesis among all ideas in the cluster
  // (the most recently analyzed one that actually merged)
  Map<String, dynamic>? get _synth {
    final candidates = ideas
        .where((i) => i.synthesis != null &&
            (i.synthesis!['should_merge'] as bool? ?? false))
        .toList()
      ..sort((a, b) => b.updatedAt.compareTo(a.updatedAt));
    return candidates.isEmpty ? null : candidates.first.synthesis;
  }

  // The idea that owns the synthesis we're displaying
  Idea? get _anchor {
    final candidates = ideas
        .where((i) => i.synthesis != null &&
            (i.synthesis!['should_merge'] as bool? ?? false))
        .toList()
      ..sort((a, b) => b.updatedAt.compareTo(a.updatedAt));
    return candidates.isEmpty ? null : candidates.first;
  }

  @override
  Widget build(BuildContext context) {
    final synth = _synth;
    final anchor = _anchor;

    return Scaffold(
      backgroundColor: AppColors.bg,
      appBar: AppBar(
        backgroundColor: AppColors.bg,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, size: 18, color: AppColors.textMuted),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(
          'Cluster #${cluster.id}  ·  ${ideas.length} notes',
          style: const TextStyle(color: AppColors.textMuted, fontSize: 14),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Bigger picture
          if (synth?['cluster_narrative'] != null)
            _NarrativeCard(text: synth!['cluster_narrative'] as String),

          // Super idea
          if (cluster.superIdea != null) ...[
            const SizedBox(height: 12),
            _Section(
              label: 'SUPER IDEA',
              accentAmber: true,
              child: Text(cluster.superIdea!,
                style: const TextStyle(color: AppColors.text, fontSize: 14, height: 1.55)),
            ),
          ],

          // Idea roles
          if (synth?['idea_roles'] != null) ...[
            const SizedBox(height: 14),
            const _Label('ROLE OF EACH IDEA'),
            const SizedBox(height: 8),
            ..._buildRoles(synth!['idea_roles'], anchor),
          ],

          // How they differ
          if (synth?['distinction_analysis'] != null) ...[
            const SizedBox(height: 12),
            _Section(
              label: 'HOW THEY DIFFER',
              child: Text(synth!['distinction_analysis'] as String,
                style: const TextStyle(color: AppColors.textMuted, fontSize: 13, height: 1.55)),
            ),
          ],

          // Relationship badge
          if (synth?['relationship_type'] != null) ...[
            const SizedBox(height: 12),
            Row(children: [
              const _Label('RELATIONSHIP'),
              const SizedBox(width: 10),
              _RelationshipBadge(type: synth!['relationship_type'] as String),
            ]),
          ],

          // Merge reasoning
          if (cluster.mergeReasoning != null) ...[
            const SizedBox(height: 12),
            _Section(
              label: 'WHY THESE CONNECT',
              child: Text(cluster.mergeReasoning!,
                style: const TextStyle(color: AppColors.textMuted, fontSize: 13, height: 1.55)),
            ),
          ],

          // Notes in this cluster — tappable
          if (ideas.isNotEmpty) ...[
            const SizedBox(height: 14),
            _Label('NOTES IN THIS CLUSTER  ·  ${ideas.length}'),
            const SizedBox(height: 8),
            ...ideas.map((idea) => _NoteChip(
              idea: idea,
              onTap: () => Navigator.push(context,
                MaterialPageRoute(builder: (_) => NoteScreen(idea: idea))),
            )),
          ],

          const SizedBox(height: 40),
        ],
      ),
    );
  }

  List<Widget> _buildRoles(dynamic roles, Idea? anchor) {
    if (roles is! List) return [];
    return roles.map<Widget>((r) {
      if (r is! Map) return const SizedBox.shrink();
      final ideaId = r['idea_id'];

      // Resolve the idea this role belongs to
      Idea? match;
      if (ideaId == 'new' || ideaId == null) {
        match = anchor;
      } else {
        try {
          match = ideas.firstWhere((i) => i.id == ideaId);
        } catch (_) {
          match = null;
        }
      }
      final title = match?.title.isEmpty == false
          ? match!.title
          : (match?.rawIdea.split(' ').take(6).join(' ') ?? 'Note');

      return Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: AppColors.border, width: 0.5),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              Container(
                width: 6, height: 6,
                decoration: const BoxDecoration(color: AppColors.green, shape: BoxShape.circle),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(title,
                  style: const TextStyle(color: AppColors.text, fontSize: 12,
                      fontWeight: FontWeight.w600),
                  overflow: TextOverflow.ellipsis),
              ),
            ]),
            if (r['core_mechanism'] != null) ...[
              const SizedBox(height: 8),
              _RoleRow(label: 'Mechanism',    value: r['core_mechanism']      as String),
            ],
            if (r['unique_contribution'] != null) ...[
              const SizedBox(height: 4),
              _RoleRow(label: 'Contribution', value: r['unique_contribution'] as String),
            ],
            if (r['surface_framing'] != null) ...[
              const SizedBox(height: 4),
              _RoleRow(label: 'Framing',      value: r['surface_framing']     as String),
            ],
          ],
        ),
      );
    }).toList();
  }
}

// ── Sub-widgets ───────────────────────────────────────────────

class _NarrativeCard extends StatelessWidget {
  final String text;
  const _NarrativeCard({required this.text});

  @override Widget build(BuildContext context) => Container(
    width: double.infinity,
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      color: AppColors.amberDim,
      borderRadius: BorderRadius.circular(12),
      border: Border.all(color: AppColors.amber.withOpacity(0.25), width: 0.5),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('THE BIGGER PICTURE', style: TextStyle(
          color: AppColors.amber, fontSize: 10,
          fontWeight: FontWeight.w600, letterSpacing: 1.0,
        )),
        const SizedBox(height: 10),
        Text(text, style: const TextStyle(color: AppColors.text, fontSize: 14, height: 1.6)),
      ],
    ),
  );
}

class _Section extends StatelessWidget {
  final String label;
  final Widget child;
  final bool   accentAmber;
  const _Section({required this.label, required this.child, this.accentAmber = false});

  @override Widget build(BuildContext context) => Container(
    width: double.infinity,
    padding: const EdgeInsets.all(14),
    decoration: BoxDecoration(
      color: AppColors.surface,
      borderRadius: BorderRadius.circular(10),
      border: Border.all(
        color: accentAmber ? AppColors.amber.withOpacity(0.3) : AppColors.border,
        width: 0.5,
      ),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(color: AppColors.textDim, fontSize: 11)),
        const SizedBox(height: 8),
        child,
      ],
    ),
  );
}

class _Label extends StatelessWidget {
  final String text;
  const _Label(this.text);
  @override Widget build(BuildContext context) => Text(text, style: const TextStyle(
    color: AppColors.textDim, fontSize: 10,
    fontWeight: FontWeight.w600, letterSpacing: 0.8,
  ));
}

class _RoleRow extends StatelessWidget {
  final String label;
  final String value;
  const _RoleRow({required this.label, required this.value});

  @override Widget build(BuildContext context) => Row(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      SizedBox(width: 88,
        child: Text(label, style: const TextStyle(color: AppColors.textDim, fontSize: 11))),
      Expanded(child: Text(value,
        style: const TextStyle(color: AppColors.textMuted, fontSize: 12, height: 1.5))),
    ],
  );
}

class _RelationshipBadge extends StatelessWidget {
  final String type;
  const _RelationshipBadge({required this.type});

  Color get _color => switch (type) {
    'complementary' => AppColors.green,
    'evolutionary'  => AppColors.amber,
    'variations'    => AppColors.textDim,
    'divergent'     => AppColors.red,
    _               => AppColors.textDim,
  };

  @override Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
    decoration: BoxDecoration(
      color: _color.withOpacity(0.12),
      borderRadius: BorderRadius.circular(6),
      border: Border.all(color: _color.withOpacity(0.4), width: 0.5),
    ),
    child: Text(type, style: TextStyle(
      color: _color, fontSize: 11, fontWeight: FontWeight.w500,
    )),
  );
}

class _NoteChip extends StatelessWidget {
  final Idea         idea;
  final VoidCallback onTap;
  const _NoteChip({required this.idea, required this.onTap});

  @override Widget build(BuildContext context) => GestureDetector(
    onTap: onTap,
    child: Container(
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppColors.border, width: 0.5),
      ),
      child: Row(children: [
        Container(width: 6, height: 6,
          decoration: const BoxDecoration(color: AppColors.green, shape: BoxShape.circle)),
        const SizedBox(width: 10),
        Expanded(child: Text(
          idea.title.isEmpty ? idea.rawIdea.split(' ').take(8).join(' ') : idea.title,
          style: const TextStyle(color: AppColors.text, fontSize: 13),
          overflow: TextOverflow.ellipsis,
        )),
        const Icon(Icons.arrow_forward_ios, size: 12, color: AppColors.textDim),
      ]),
    ),
  );
}
