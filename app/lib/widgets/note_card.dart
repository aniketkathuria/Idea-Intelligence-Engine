import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/idea.dart';
import '../theme/app_theme.dart';

class NoteCard extends StatelessWidget {
  final Idea idea;
  final VoidCallback onTap;
  final VoidCallback onDelete;

  const NoteCard({
    super.key,
    required this.idea,
    required this.onTap,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 5),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.border, width: 0.5),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    idea.title,
                    style: const TextStyle(
                      color: AppColors.text,
                      fontSize: 15,
                      fontWeight: FontWeight.w500,
                      height: 1.3,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                const SizedBox(width: 8),
                _StatusDot(idea: idea),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              idea.preview,
              style: const TextStyle(
                color: AppColors.textMuted,
                fontSize: 13,
                height: 1.5,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                Text(
                  _formatDate(idea.updatedAt),
                  style: const TextStyle(color: AppColors.textDim, fontSize: 11),
                ),
                if (idea.category != null) ...[
                  const SizedBox(width: 8),
                  _CategoryBadge(category: idea.category!),
                ],
                const Spacer(),
                GestureDetector(
                  onTap: onDelete,
                  child: const Icon(Icons.delete_outline,
                      size: 16, color: AppColors.textDim),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  String _formatDate(DateTime dt) {
    final now = DateTime.now();
    if (dt.year == now.year && dt.month == now.month && dt.day == now.day) {
      return DateFormat('h:mm a').format(dt);
    }
    if (dt.year == now.year) {
      return DateFormat('MMM d').format(dt);
    }
    return DateFormat('MMM d, y').format(dt);
  }
}

class _StatusDot extends StatelessWidget {
  final Idea idea;
  const _StatusDot({required this.idea});

  @override
  Widget build(BuildContext context) {
    if (idea.isProcessing) {
      return const SizedBox(
        width: 8, height: 8,
        child: CircularProgressIndicator(
          strokeWidth: 1.5,
          color: AppColors.amber,
        ),
      );
    }
    if (idea.isAnalyzed) {
      return Container(
        width: 7, height: 7,
        decoration: const BoxDecoration(
          color: AppColors.green, shape: BoxShape.circle,
        ),
      );
    }
    if (idea.isFailed) {
      return Container(
        width: 7, height: 7,
        decoration: const BoxDecoration(
          color: AppColors.red, shape: BoxShape.circle,
        ),
      );
    }
    return Container(
      width: 7, height: 7,
      decoration: BoxDecoration(
        color: AppColors.textDim,
        shape: BoxShape.circle,
        border: Border.all(color: AppColors.border2, width: 0.5),
      ),
    );
  }
}

class _CategoryBadge extends StatelessWidget {
  final String category;
  const _CategoryBadge({required this.category});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: AppColors.amberDim,
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: AppColors.amber.withOpacity(0.3), width: 0.5),
      ),
      child: Text(
        category,
        style: const TextStyle(
          color: AppColors.amber,
          fontSize: 10,
          fontWeight: FontWeight.w500,
          letterSpacing: 0.3,
        ),
      ),
    );
  }
}
