import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../core/app_state.dart';
import '../models/task.dart';

class TasksScreen extends StatelessWidget {
  const TasksScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    // Show only active (non-completed) tasks on the main dashboard
    final tasks = state.tasks.where((t) => !t.isCompleted).toList();
    final colors = Theme.of(context).colorScheme;

    return Scaffold(
      backgroundColor: Colors.transparent, // Background handled by HomeScreen
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showTaskEditor(context),
        backgroundColor: colors.primary,
        foregroundColor: colors.onPrimary,
        icon: const Icon(Icons.add_rounded),
        label: Text(
          'New Task',
          style: GoogleFonts.montserrat(fontWeight: FontWeight.w600),
        ),
      ).animate().scale(delay: 400.ms, curve: Curves.easeOutBack),
      body: tasks.isEmpty
          ? _buildEmptyState(context)
          : ListView.builder(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
              itemCount: tasks.length,
              itemBuilder: (context, index) {
                return _TaskCard(task: tasks[index])
                    .animate()
                    .fadeIn(delay: (index * 50).ms, duration: 400.ms)
                    .slideY(begin: 0.1, end: 0);
              },
            ),
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.all(32),
            decoration: BoxDecoration(
              color: colors.primaryContainer.withValues(alpha: 0.2),
              shape: BoxShape.circle,
            ),
            child: Icon(Icons.task_alt_rounded, size: 80, color: colors.primary.withValues(alpha: 0.6)),
          ).animate().scale(duration: 600.ms, curve: Curves.elasticOut),
          const SizedBox(height: 24),
          Text(
            'Your list is clear!',
            style: GoogleFonts.montserrat(
              fontWeight: FontWeight.w700,
              fontSize: 22,
              color: colors.onSurface,
            ),
          ).animate().fadeIn(delay: 200.ms),
          const SizedBox(height: 12),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 48),
            child: Text(
              'No pending reminders. Tap the + button to stay organized.',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: colors.onSurfaceVariant,
                fontSize: 15,
                height: 1.5,
              ),
            ),
          ).animate().fadeIn(delay: 400.ms),
        ],
      ),
    );
  }
}

class _TaskCard extends StatelessWidget {
  const _TaskCard({required this.task});

  final TaskItem task;

  @override
  Widget build(BuildContext context) {
    final state = context.read<AppState>();
    final colors = Theme.of(context).colorScheme;
    final due = DateFormat('EEE, MMM d • h:mm a').format(task.dueAt);
    final isOverdue = task.isOverdue == 1;
    final priorityColor = Color(task.priorityColorValue);

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Dismissible(
        key: ValueKey(task.id),
        direction: DismissDirection.horizontal,
        background: _buildSwipeAction(
          color: Colors.green,
          icon: Icons.check_circle_rounded,
          alignment: Alignment.centerLeft,
        ),
        secondaryBackground: _buildSwipeAction(
          color: Colors.redAccent,
          icon: Icons.delete_sweep_rounded,
          alignment: Alignment.centerRight,
        ),
        onDismissed: (direction) {
          if (direction == DismissDirection.startToEnd) {
            state.completeTask(task);
          } else {
            state.deleteTask(task);
          }
        },
        child: Container(
          decoration: BoxDecoration(
            color: colors.surface,
            borderRadius: BorderRadius.circular(22),
            boxShadow: [
              BoxShadow(
                color: (isOverdue ? colors.error : priorityColor).withValues(alpha: 0.08),
                blurRadius: 24,
                spreadRadius: -4,
                offset: const Offset(0, 12),
              ),
            ],
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(22),
            child: Stack(
              children: [
                // ── Priority Strip ──────────────────────────────────────
                Positioned(
                  left: 0, top: 0, bottom: 0,
                  child: Container(
                    width: 6,
                    decoration: BoxDecoration(
                      color: isOverdue ? colors.error : priorityColor,
                      borderRadius: const BorderRadius.horizontal(left: Radius.circular(20)),
                    ),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(18, 16, 12, 12),
                  child: Column(
                    children: [
                      Row(
                        children: [
                          _CategoryIcon(task: task),
                          const SizedBox(width: 16),
                          Expanded(
                            child: InkWell(
                              onTap: () => _showTaskEditor(context, task),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    task.title,
                                    style: GoogleFonts.outfit(
                                      fontWeight: FontWeight.w700,
                                      fontSize: 17,
                                      color: colors.onSurface,
                                      letterSpacing: -0.2,
                                    ),
                                  ),
                                  Row(
                                    children: [
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                        decoration: BoxDecoration(
                                          color: task.displayStatus == 'Missed' 
                                            ? colors.error.withValues(alpha: 0.1)
                                            : task.displayStatus == 'Due Now'
                                              ? Colors.orange.withValues(alpha: 0.1)
                                              : colors.surfaceContainerHighest.withValues(alpha: 0.5),
                                          borderRadius: BorderRadius.circular(6),
                                        ),
                                        child: Row(
                                          children: [
                                            Icon(
                                              task.displayStatus == 'Missed' ? Icons.warning_amber_rounded : Icons.timer_outlined,
                                              size: 12,
                                              color: task.displayStatus == 'Missed' ? colors.error : task.displayStatus == 'Due Now' ? Colors.orange : colors.onSurfaceVariant.withValues(alpha: 0.7),
                                            ),
                                            const SizedBox(width: 4),
                                            Text(
                                              task.displayStatus == 'Missed' ? 'Missed' : task.displayStatus == 'Due Now' ? 'Due Now' : due,
                                              style: GoogleFonts.outfit(
                                                fontSize: 11,
                                                fontWeight: FontWeight.w800,
                                                color: task.displayStatus == 'Missed' ? colors.error : task.displayStatus == 'Due Now' ? Colors.orange : colors.onSurfaceVariant,
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                          ),
                          _CompleteButton(task: task),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.end,
                        children: [
                          _QuickAction(
                            icon: Icons.snooze_rounded,
                            label: 'Snooze',
                            color: colors.primary,
                            onTap: () => _showSnoozeMenu(context, state, task),
                          ),
                          const SizedBox(width: 12),
                          _QuickAction(
                            icon: Icons.delete_outline_rounded,
                            label: 'Delete',
                            color: colors.onSurfaceVariant.withValues(alpha: 0.5),
                            onTap: () => state.deleteTask(task),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildSwipeAction({
    required Color color,
    required IconData icon,
    required Alignment alignment,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(20),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 24),
      alignment: alignment,
      child: Icon(icon, color: Colors.white, size: 28),
    );
  }
}

class _CompleteButton extends StatelessWidget {
  const _CompleteButton({required this.task});
  final TaskItem task;

  @override
  Widget build(BuildContext context) {
    final state = context.read<AppState>();
    final colors = Theme.of(context).colorScheme;
    return IconButton(
      onPressed: () => state.toggleTask(task),
      icon: Container(
        padding: const EdgeInsets.all(4),
        decoration: BoxDecoration(
          border: Border.all(color: colors.primary.withValues(alpha: 0.5), width: 2),
          shape: BoxShape.circle,
        ),
        child: Icon(Icons.check_rounded, size: 16, color: colors.primary),
      ),
    );
  }
}

void _showSnoozeMenu(BuildContext context, AppState state, TaskItem task) {
  showModalBottomSheet(
    context: context,
    backgroundColor: Colors.transparent,
    builder: (ctx) => Container(
      decoration: BoxDecoration(
        color: Theme.of(context).scaffoldBackgroundColor,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text('Snooze Task', style: GoogleFonts.outfit(fontWeight: FontWeight.w800, fontSize: 20)),
          const SizedBox(height: 16),
          _SnoozeOption(label: '5 Minutes', icon: Icons.timer_outlined, onTap: () => {state.snoozeTask(task, 5), Navigator.pop(ctx)}),
          _SnoozeOption(label: '10 Minutes', icon: Icons.timer_outlined, onTap: () => {state.snoozeTask(task, 10), Navigator.pop(ctx)}),
          _SnoozeOption(label: '30 Minutes', icon: Icons.timer_outlined, onTap: () => {state.snoozeTask(task, 30), Navigator.pop(ctx)}),
          _SnoozeOption(label: 'Tomorrow', icon: Icons.event_repeat_rounded, onTap: () => {state.snoozeTask(task, 1440), Navigator.pop(ctx)}),
          const SizedBox(height: 16),
        ],
      ),
    ),
  );
}

class _SnoozeOption extends StatelessWidget {
  const _SnoozeOption({required this.label, required this.icon, required this.onTap});
  final String label;
  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon),
      title: Text(label, style: const TextStyle(fontWeight: FontWeight.w600)),
      onTap: onTap,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
    );
  }
}

class _CategoryIcon extends StatelessWidget {
  const _CategoryIcon({required this.task});
  final TaskItem task;

  @override
  Widget build(BuildContext context) {
    final catColor = task.categoryColor;
    return Container(
      width: 48,
      height: 48,
      decoration: BoxDecoration(
        color: catColor.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: catColor.withValues(alpha: 0.1), width: 1),
      ),
      child: Center(
        child: Icon(task.categoryIcon, color: catColor, size: 24),
      ),
    );
  }
}

void _showTaskEditor(BuildContext context, [TaskItem? task]) {
  showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    builder: (ctx) => _TaskEditorSheet(task: task),
  );
}

class _TaskEditorSheet extends StatefulWidget {
  const _TaskEditorSheet({this.task});
  final TaskItem? task;

  @override
  State<_TaskEditorSheet> createState() => _TaskEditorSheetState();
}

class _TaskEditorSheetState extends State<_TaskEditorSheet> {
  late TextEditingController _title;
  late DateTime _due;
  late int _priority;
  late String _category;
  String? _error;

  @override
  void initState() {
    super.initState();
    _title = TextEditingController(text: widget.task?.title ?? '');
    _due = widget.task?.dueAt ?? DateTime.now();
    _priority = widget.task?.priority ?? 2;
    _category = widget.task?.category ?? 'General';
  }

  @override
  Widget build(BuildContext context) {
    final state = context.read<AppState>();
    final colors = Theme.of(context).colorScheme;

    return Container(
      decoration: BoxDecoration(
        color: Theme.of(context).scaffoldBackgroundColor,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
      ),
      padding: EdgeInsets.only(
        top: 24,
        left: 24,
        right: 24,
        bottom: MediaQuery.of(context).viewInsets.bottom + 32,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Text(
                widget.task == null ? 'New Task' : 'Edit Task',
                style: GoogleFonts.montserrat(
                  fontWeight: FontWeight.w800,
                  fontSize: 22,
                ),
              ),
              const Spacer(),
              IconButton(
                onPressed: () => Navigator.pop(context),
                icon: const Icon(Icons.close_rounded),
                style: IconButton.styleFrom(
                  backgroundColor: colors.surfaceContainerHighest,
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
          TextField(
            controller: _title,
            autofocus: true,
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
            decoration: InputDecoration(
              hintText: 'What needs to be done?',
              prefixIcon: const Icon(Icons.edit_note_rounded),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
            ),
          ),
          const SizedBox(height: 16),
          _buildDateTimePicker(context),
          const SizedBox(height: 16),
          _buildPrioritySelector(colors),
          const SizedBox(height: 16),
          _buildCategorySelector(colors),
          if (_error != null) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: colors.errorContainer.withValues(alpha: 0.5),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: colors.error.withValues(alpha: 0.3)),
              ),
              child: Row(
                children: [
                  Icon(Icons.error_outline_rounded, color: colors.error, size: 20),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      _error!,
                      style: TextStyle(color: colors.onErrorContainer, fontSize: 13, fontWeight: FontWeight.w600),
                    ),
                  ),
                ],
              ),
            ),
          ],
          const SizedBox(height: 24),
          FilledButton(
            onPressed: () async {
              if (_title.text.trim().isEmpty) {
                setState(() => _error = 'Please enter a task title');
                return;
              }
              
              // Validate that the date is in the future
              if (_due.isBefore(DateTime.now().subtract(const Duration(minutes: 1)))) {
                setState(() => _error = 'Please select a future date and time!');
                return;
              }

              setState(() => _error = null);
              final draft = TaskDraft(
                title: _title.text.trim(),
                dueIso: _due.toUtc().toIso8601String(),
                priority: _priority,
                category: _category,
              );
              if (widget.task == null) {
                await state.createTask(draft);
              } else {
                await state.updateTask(widget.task!.id, draft);
              }
              if (mounted) Navigator.pop(context);
            },
            child: state.isLoading
                ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : Text(widget.task == null ? 'Create Task' : 'Save Changes'),
          ),
        ],
      ),
    );
  }

  Widget _buildDateTimePicker(BuildContext context) {
    final dateStr = DateFormat('EEE, MMM d').format(_due);
    final timeStr = DateFormat('h:mm a').format(_due);

    return Row(
      children: [
        Expanded(
          child: _EditorTile(
            label: 'Date',
            value: dateStr,
            icon: Icons.calendar_today_rounded,
            onTap: () async {
              final picked = await showDatePicker(
                context: context,
                initialDate: _due,
                firstDate: DateTime.now(),
                lastDate: DateTime.now().add(const Duration(days: 365)),
              );
              if (picked != null) {
                setState(() => _due = DateTime(picked.year, picked.month, picked.day, _due.hour, _due.minute));
              }
            },
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _EditorTile(
            label: 'Time',
            value: timeStr,
            icon: null, // Removed icon as requested
            onTap: () async {
              final picked = await showTimePicker(
                context: context,
                initialTime: TimeOfDay.fromDateTime(_due),
                initialEntryMode: TimePickerEntryMode.inputOnly,
              );
              if (picked != null) {
                setState(() => _due = DateTime(_due.year, _due.month, _due.day, picked.hour, picked.minute));
              }
            },
          ),
        ),
      ],
    );
  }

  Widget _buildPrioritySelector(ColorScheme colors) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Priority', style: GoogleFonts.montserrat(fontWeight: FontWeight.w700, fontSize: 13, color: colors.primary)),
        const SizedBox(height: 8),
        SegmentedButton<int>(
          segments: const [
            ButtonSegment(value: 1, label: Text('High'), icon: Icon(Icons.priority_high_rounded, size: 16)),
            ButtonSegment(value: 2, label: Text('Med'), icon: Icon(Icons.remove_rounded, size: 16)),
            ButtonSegment(value: 3, label: Text('Low'), icon: Icon(Icons.low_priority_rounded, size: 16)),
          ],
          selected: {_priority},
          onSelectionChanged: (set) => setState(() => _priority = set.first),
          showSelectedIcon: false,
          style: SegmentedButton.styleFrom(
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        ),
      ],
    );
  }

  Widget _buildCategorySelector(ColorScheme colors) {
    final cats = [
      'General',
      'Work',
      'Study',
      'Gym',
      'Health',
      'Personal',
      'Call',
      'Family',
      'Social',
      'Finance',
      'Home',
      'Meeting',
      'Gaming',
      'Birthday'
    ];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Category', style: GoogleFonts.montserrat(fontWeight: FontWeight.w700, fontSize: 13, color: colors.primary)),
        const SizedBox(height: 8),
        SizedBox(
          height: 40,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: cats.length,
            separatorBuilder: (_, __) => const SizedBox(width: 8),
            itemBuilder: (context, i) {
              final active = _category == cats[i];
              return ChoiceChip(
                label: Text(cats[i]),
                selected: active,
                onSelected: (val) => setState(() => _category = cats[i]),
                showCheckmark: false,
                labelStyle: TextStyle(
                  color: active ? colors.onPrimary : colors.onSurfaceVariant,
                  fontWeight: active ? FontWeight.w700 : FontWeight.w500,
                ),
                selectedColor: colors.primary,
                backgroundColor: colors.surfaceContainerHighest,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              );
            },
          ),
        ),
      ],
    );
  }
}

class _EditorTile extends StatelessWidget {
  const _EditorTile({required this.label, required this.value, this.icon, required this.onTap});
  final String label, value;
  final IconData? icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: colors.surfaceContainerHighest.withValues(alpha: 0.5),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: colors.outlineVariant.withValues(alpha: 0.5)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: colors.onSurfaceVariant)),
            const SizedBox(height: 4),
            Row(
              children: [
                if (icon != null) ...[
                  Icon(icon, size: 16, color: colors.primary),
                  const SizedBox(width: 8),
                ],
                Text(value, style: const TextStyle(fontWeight: FontWeight.w700)),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _QuickAction extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  const _QuickAction({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 16, color: color),
            const SizedBox(width: 6),
            Text(
              label,
              style: GoogleFonts.outfit(
                fontSize: 12,
                fontWeight: FontWeight.w700,
                color: color,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
