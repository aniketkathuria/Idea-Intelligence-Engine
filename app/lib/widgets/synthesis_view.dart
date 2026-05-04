import 'package:flutter/material.dart';
import '../models/idea.dart';
import '../models/cluster.dart';
import '../theme/app_theme.dart';

class SynthesisView extends StatelessWidget {
  final Idea       idea;
  final Cluster?   cluster;
  final List<Idea> clusterIdeas;

  const SynthesisView({
    super.key,
    required this.idea,
    this.cluster,
    this.clusterIdeas = const [],
  });

  @override
  Widget build(BuildContext context) {
    final synth = idea.synthesis;

    if (idea.status == 'processing') {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              SizedBox(
                width: 36, height: 36,
                child: CircularProgressIndicator(color: AppColors.amber, strokeWidth: 2),
              ),
              SizedBox(height: 20),
              Text('Processing…', style: TextStyle(color: AppColors.amber, fontSize: 14)),
            ],
          ),
        ),
      );
    }

    if (synth == null && cluster == null) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(32),
          child: Text(
            'No synthesis yet.\nAnalyze the note first — if similar ideas exist, they\'ll be connected here.',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.textDim, fontSize: 14, height: 1.6),
          ),
        ),
      );
    }

    final shouldMerge = synth?['should_merge'] as bool? ?? false;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Cluster narrative — the big picture
        if (shouldMerge && synth?['cluster_narrative'] != null)
          _NarrativeCard(text: synth!['cluster_narrative'] as String),

        // Super idea
        if (cluster?.superIdea != null) ...[
          const SizedBox(height: 14),
          _Section(
            label: 'SUPER IDEA',
            accentColor: AppColors.amber,
            child: Text(cluster!.superIdea!,
              style: const TextStyle(color: AppColors.text, fontSize: 14, height: 1.55)),
          ),
        ],

        // Idea roles
        if (shouldMerge && synth?['idea_roles'] != null) ...[
          const SizedBox(height: 14),
          const _Label('ROLE OF EACH IDEA'),
          const SizedBox(height: 8),
          ..._buildRoles(synth!['idea_roles'], idea, clusterIdeas),
        ],

        // Distinction analysis
        if (synth?['distinction_analysis'] != null) ...[
          const SizedBox(height: 14),
          _Section(
            label: 'HOW THEY DIFFER',
            child: Text(synth!['distinction_analysis'] as String,
              style: const TextStyle(color: AppColors.textMuted, fontSize: 13, height: 1.55)),
          ),
        ],

        // Relationship type badge
        if (synth?['relationship_type'] != null) ...[
          const SizedBox(height: 14),
          Row(children: [
            const _Label('RELATIONSHIP'),
            const SizedBox(width: 10),
            _RelationshipBadge(type: synth!['relationship_type'] as String),
          ]),
        ],

        // Merge reasoning
        if (synth?['merge_reasoning'] != null) ...[
          const SizedBox(height: 14),
          _Section(
            label: shouldMerge ? 'WHY THESE CONNECT' : 'WHY NOT MERGED',
            child: Text(synth!['merge_reasoning'] as String,
              style: const TextStyle(color: AppColors.textMuted, fontSize: 13, height: 1.55)),
          ),
        ],

        // Connected notes
        if (cluster != null && clusterIdeas.isNotEmpty) ...[
          const SizedBox(height: 14),
          _Label('CONNECTED NOTES  ·  ${clusterIdeas.length}'),
          const SizedBox(height: 8),
          ...clusterIdeas.map((i) => _NoteChip(idea: i)),
        ],

        // Not merged state
        if (!shouldMerge && synth != null) ...[
          const SizedBox(height: 14),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: AppColors.border, width: 0.5),
            ),
            child: Row(
              children: [
                Container(
                  width: 6, height: 6,
                  decoration: const BoxDecoration(
                    color: AppColors.textDim, shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 10),
                const Expanded(
                  child: Text(
                    'This idea stands on its own — no strong cluster connection found.',
                    style: TextStyle(color: AppColors.textMuted, fontSize: 13, height: 1.5),
                  ),
                ),
              ],
            ),
          ),
        ],

        const SizedBox(height: 40),
      ],
    );
  }

  List<Widget> _buildRoles(
    dynamic roles,
    Idea currentIdea,
    List<Idea> clusterIdeas,
  ) {
    if (roles is! List) return [];
    return roles.map<Widget>((r) {
      if (r is! Map) return const SizedBox.shrink();
      final ideaId  = r['idea_id'];
      final isNew   = ideaId == 'new' || ideaId == null;

      // Find the label for this role
      String noteTitle;
      if (isNew) {
        noteTitle = currentIdea.title.isEmpty ? 'This note' : currentIdea.title;
      } else {
        final match = clusterIdeas.where((i) => i.id == ideaId).toList();
        noteTitle = match.isNotEmpty ? match.first.title : 'Note #$ideaId';
      }

      return Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: isNew
                ? AppColors.amber.withOpacity(0.3)
                : AppColors.border,
            width: 0.5,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              Container(
                width: 6, height: 6,
                decoration: BoxDecoration(
                  color: isNew ? AppColors.amber : AppColors.green,
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  noteTitle,
                  style: TextStyle(
                    color: isNew ? AppColors.amber : AppColors.text,
                    fontSize: 12, fontWeight: FontWeight.w600,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ]),
            if (r['core_mechanism'] != null) ...[
              const SizedBox(height: 8),
              _RoleRow(label: 'Mechanism', value: r['core_mechanism'] as String),
            ],
            if (r['unique_contribution'] != null) ...[
              const SizedBox(height: 4),
              _RoleRow(label: 'Contribution', value: r['unique_contribution'] as String),
            ],
            if (r['surface_framing'] != null) ...[
              const SizedBox(height: 4),
              _RoleRow(label: 'Framing', value: r['surface_framing'] as String),
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
        Text(text, style: const TextStyle(
          color: AppColors.text, fontSize: 14, height: 1.6,
        )),
      ],
    ),
  );
}

class _Section extends StatelessWidget {
  final String  label;
  final Widget  child;
  final Color   accentColor;
  const _Section({required this.label, required this.child, this.accentColor = AppColors.border});

  @override Widget build(BuildContext context) => Container(
    width: double.infinity,
    padding: const EdgeInsets.all(14),
    decoration: BoxDecoration(
      color: AppColors.surface,
      borderRadius: BorderRadius.circular(10),
      border: Border.all(color: accentColor.withOpacity(accentColor == AppColors.border ? 1 : 0.3), width: 0.5),
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
      SizedBox(
        width: 88,
        child: Text(label, style: const TextStyle(
          color: AppColors.textDim, fontSize: 11,
        )),
      ),
      Expanded(child: Text(value, style: const TextStyle(
        color: AppColors.textMuted, fontSize: 12, height: 1.5,
      ))),
    ],
  );
}

class _RelationshipBadge extends StatelessWidget {
  final String type;
  const _RelationshipBadge({required this.type});

  Color get _color {
    switch (type) {
      case 'complementary': return AppColors.green;
      case 'evolutionary':  return AppColors.amber;
      case 'variations':    return AppColors.textDim;
      case 'divergent':     return AppColors.red;
      default:              return AppColors.textDim;
    }
  }

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
  final Idea idea;
  const _NoteChip({required this.idea});

  @override Widget build(BuildContext context) => Container(
    margin: const EdgeInsets.only(bottom: 6),
    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
    decoration: BoxDecoration(
      color: AppColors.surface,
      borderRadius: BorderRadius.circular(8),
      border: Border.all(color: AppColors.border, width: 0.5),
    ),
    child: Row(children: [
      Container(
        width: 6, height: 6,
        decoration: const BoxDecoration(color: AppColors.green, shape: BoxShape.circle),
      ),
      const SizedBox(width: 10),
      Expanded(child: Text(idea.title,
        style: const TextStyle(color: AppColors.text, fontSize: 13),
        overflow: TextOverflow.ellipsis,
      )),
    ]),
  );
}
