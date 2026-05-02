import 'package:flutter/material.dart';
import '../models/idea.dart';
import '../models/cluster.dart';
import '../theme/app_theme.dart';

class SynthesisView extends StatelessWidget {
  final Idea    idea;
  final Cluster? cluster;
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

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (cluster != null) _ClusterCard(cluster: cluster!, ideas: clusterIdeas),
        if (synth != null) ...[
          const SizedBox(height: 16),
          _SynthesisCard(synth: synth),
        ],
        const SizedBox(height: 40),
      ],
    );
  }
}

class _ClusterCard extends StatelessWidget {
  final Cluster    cluster;
  final List<Idea> ideas;
  const _ClusterCard({required this.cluster, required this.ideas});

  @override Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Icon(Icons.hub_outlined, color: AppColors.amber, size: 14),
            const SizedBox(width: 6),
            Text(
              'CLUSTER #${cluster.id}  ·  ${ideas.length} CONNECTED NOTES',
              style: const TextStyle(
                color: AppColors.amber, fontSize: 10,
                fontWeight: FontWeight.w600, letterSpacing: 1.0,
              ),
            ),
          ],
        ),
        if (cluster.superIdea != null) ...[
          const SizedBox(height: 12),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: AppColors.amber.withOpacity(0.2), width: 0.5),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Super Idea', style: TextStyle(
                  color: AppColors.textDim, fontSize: 11,
                )),
                const SizedBox(height: 6),
                Text(cluster.superIdea!, style: const TextStyle(
                  color: AppColors.text, fontSize: 14, height: 1.55,
                )),
              ],
            ),
          ),
        ],
        if (cluster.mergeReasoning != null) ...[
          const SizedBox(height: 10),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: AppColors.border, width: 0.5),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Why these connect', style: TextStyle(
                  color: AppColors.textDim, fontSize: 11,
                )),
                const SizedBox(height: 6),
                Text(cluster.mergeReasoning!, style: const TextStyle(
                  color: AppColors.textMuted, fontSize: 13, height: 1.55,
                )),
              ],
            ),
          ),
        ],
        if (ideas.isNotEmpty) ...[
          const SizedBox(height: 14),
          const Text('CONNECTED NOTES', style: TextStyle(
            color: AppColors.textDim, fontSize: 10,
            fontWeight: FontWeight.w600, letterSpacing: 0.8,
          )),
          const SizedBox(height: 8),
          ...ideas.map((i) => Container(
            margin: const EdgeInsets.only(bottom: 6),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: AppColors.border, width: 0.5),
            ),
            child: Row(
              children: [
                Container(
                  width: 6, height: 6,
                  decoration: const BoxDecoration(
                    color: AppColors.green, shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(child: Text(
                  i.title,
                  style: const TextStyle(color: AppColors.text, fontSize: 13),
                )),
              ],
            ),
          )),
        ],
      ],
    );
  }
}

class _SynthesisCard extends StatelessWidget {
  final Map<String, dynamic> synth;
  const _SynthesisCard({required this.synth});

  @override Widget build(BuildContext context) {
    final shouldMerge = synth['should_merge'] as bool? ?? false;
    if (!shouldMerge) {
      return Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: AppColors.border, width: 0.5),
        ),
        child: const Text(
          'Synthesis ran but no strong connection was found with existing notes.',
          style: TextStyle(color: AppColors.textMuted, fontSize: 13, height: 1.5),
        ),
      );
    }
    return const SizedBox.shrink(); // Cluster card above covers the content
  }
}
