import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../core/app_state.dart';
import '../models/task.dart';

class HistoryScreen extends StatelessWidget {
  const HistoryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    // History should only show completed tasks
    final completedTasks = state.tasks.where((t) => t.isCompleted).toList();
    final colors = Theme.of(context).colorScheme;

    return Scaffold(
      backgroundColor: Colors.transparent,
      floatingActionButton: completedTasks.isNotEmpty
          ? FloatingActionButton.extended(
              onPressed: () => _showClearAllDialog(context, state),
              backgroundColor: Colors.redAccent.withValues(alpha: 0.1),
              elevation: 0,
              icon: const Icon(Icons.delete_sweep_rounded,
                  color: Colors.redAccent),
              label: const Text('Clear All',
                  style: TextStyle(
                      color: Colors.redAccent, fontWeight: FontWeight.w700)),
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                  side: const BorderSide(color: Colors.redAccent, width: 1)),
            ).animate().scale(delay: 400.ms)
          : null,
      body: completedTasks.isEmpty
          ? _buildEmptyState(colors)
          : ListView.builder(
              padding: const EdgeInsets.all(20),
              itemCount: completedTasks.length,
              itemBuilder: (context, index) {
                final task = completedTasks[index];
                return _HistoryTaskCard(task: task);
              },
            ),
    );
  }

  void _showClearAllDialog(BuildContext context, AppState state) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Clear History'),
        content: const Text(
            'Are you sure you want to delete ALL completed tasks permanently?'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          FilledButton(
            onPressed: () async {
              // Close dialog first to avoid using a deactivated dialog context
              // after awaiting async work.
              Navigator.pop(ctx);
              try {
                await state.clearCompletedHistory();
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Completed tasks cleared')));
                }
              } catch (e) {
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Error clearing history: $e')));
                }
              }
            },
            style: FilledButton.styleFrom(
                backgroundColor: Theme.of(context).colorScheme.error),
            child: const Text('Delete All'),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState(ColorScheme colors) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.history_rounded,
              size: 64, color: colors.outline.withValues(alpha: 0.3)),
          const SizedBox(height: 16),
          Text(
            'No completed tasks yet',
            style: GoogleFonts.montserrat(
              fontWeight: FontWeight.w600,
              fontSize: 16,
              color: colors.onSurfaceVariant,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Finish your goals to see them here.',
            style: TextStyle(
                color: colors.onSurfaceVariant.withValues(alpha: 0.6)),
          ),
        ],
      ),
    );
  }
}

class _HistoryTaskCard extends StatelessWidget {
  const _HistoryTaskCard({required this.task});
  final TaskItem task;

  @override
  Widget build(BuildContext context) {
    final state = context.read<AppState>();
    final colors = Theme.of(context).colorScheme;

    final compDate = task.completedAt ?? DateTime.now();
    final dateInfo =
        'Finished: ${DateFormat('MMM d, h:mm a').format(compDate.toLocal())}';

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: colors.outlineVariant.withValues(alpha: 0.3),
        ),
        boxShadow: [
          BoxShadow(
            color: colors.shadow.withValues(alpha: 0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(20),
        child: InkWell(
          borderRadius: BorderRadius.circular(20),
          onTap: () => _showUndoDialog(context, state, task),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    color: task.categoryColor.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(task.categoryIcon,
                      color: task.categoryColor, size: 22),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        task.title,
                        style: GoogleFonts.montserrat(
                          fontWeight: FontWeight.w700,
                          fontSize: 15,
                          decoration: TextDecoration.lineThrough,
                          color: colors.onSurfaceVariant,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        dateInfo,
                        style: TextStyle(
                            fontSize: 12,
                            color:
                                colors.onSurfaceVariant.withValues(alpha: 0.7)),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.delete_outline_rounded,
                      color: Colors.red, size: 20),
                  tooltip: 'Delete Permanently',
                  onPressed: () => _showDeleteDialog(context, state, task),
                ),
                IconButton(
                  icon: const Icon(Icons.settings_backup_restore_rounded,
                      color: Colors.green, size: 20),
                  tooltip: 'Restore Task',
                  onPressed: () => state.toggleTask(task),
                ),
              ],
            ),
          ),
        ),
      ),
    ).animate().fadeIn(duration: 400.ms).slideX(begin: 0.05, end: 0);
  }

  void _showDeleteDialog(BuildContext context, AppState state, TaskItem task) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete Permanently?'),
        content: Text('This will remove "${task.title}" from history forever.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          FilledButton(
            onPressed: () {
              state.deleteTask(task);
              Navigator.pop(ctx);
            },
            style: FilledButton.styleFrom(
                backgroundColor: Theme.of(context).colorScheme.error),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }

  void _showUndoDialog(BuildContext context, AppState state, TaskItem task) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Undo Completion?'),
        content: Text('Move "${task.title}" back to active tasks?'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          TextButton(
            onPressed: () {
              state.toggleTask(task);
              Navigator.pop(ctx);
            },
            child: const Text('Restore'),
          ),
        ],
      ),
    );
  }
}
