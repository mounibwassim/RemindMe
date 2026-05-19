import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'package:table_calendar/table_calendar.dart';

import '../core/app_state.dart';
import '../models/task.dart';

class CalendarScreen extends StatefulWidget {
  const CalendarScreen({super.key});

  @override
  State<CalendarScreen> createState() => _CalendarScreenState();
}

class _CalendarScreenState extends State<CalendarScreen> {
  late DateTime _selectedDay;
  late DateTime _focusedDay;
  CalendarFormat _format = CalendarFormat.month;

  @override
  void initState() {
    super.initState();
    final now = DateTime.now();
    _selectedDay = DateTime(now.year, now.month, now.day);
    _focusedDay = now;
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final tasks = state.tasks;
    final colors = Theme.of(context).colorScheme;

    // Group tasks by date
    final events = _groupTasksByDate(tasks);
    final selectedTasks = events[_selectedDay] ?? [];

    return Scaffold(
      backgroundColor: Colors.transparent,
      body: CustomScrollView(
        slivers: [
          // ── Calendar Section ──────────────────────────────────────
          SliverToBoxAdapter(
            child: _buildCalendarCard(colors, events),
          ),
          
          // ── Selected Date Header ──────────────────────────────────
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(20, 24, 20, 12),
              child: Row(
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        DateFormat('EEEE, MMMM d').format(_selectedDay),
                        style: GoogleFonts.montserrat(
                          fontWeight: FontWeight.w700,
                          fontSize: 18,
                        ),
                      ),
                      Text(
                        selectedTasks.isEmpty 
                            ? 'No tasks scheduled' 
                            : '${selectedTasks.length} items to complete',
                        style: TextStyle(color: colors.onSurfaceVariant, fontSize: 13),
                      ),
                    ],
                  ),
                  const Spacer(),
                  if (selectedTasks.isNotEmpty)
                    _buildStatusChip(colors, selectedTasks),
                ],
              ),
            ).animate().fadeIn().slideX(begin: -0.05),
          ),
          
          // ── Task List Section ─────────────────────────────────────
          if (selectedTasks.isEmpty)
            SliverFillRemaining(
              hasScrollBody: false,
              child: _buildEmptyDay(colors),
            )
          else
            SliverPadding(
              padding: const EdgeInsets.only(left: 16, right: 16, bottom: 32),
              sliver: SliverList(
                delegate: SliverChildBuilderDelegate(
                  (context, i) => _CalendarTaskItem(task: selectedTasks[i])
                      .animate()
                      .fadeIn(delay: (i * 50).ms)
                      .slideY(begin: 0.1, end: 0),
                  childCount: selectedTasks.length,
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildCalendarCard(ColorScheme colors, Map<DateTime, List<TaskItem>> events) {
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 8, 16, 0),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(28),
        color: colors.surface,
        border: Border.all(
          color: colors.outlineVariant.withValues(alpha: 0.3),
        ),
        boxShadow: [
          BoxShadow(
            color: colors.primary.withValues(alpha: 0.04),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: TableCalendar(
        firstDay: DateTime.now().subtract(const Duration(days: 365)),
        lastDay: DateTime.now().add(const Duration(days: 365)),
        focusedDay: _focusedDay,
        selectedDayPredicate: (day) => isSameDay(_selectedDay, day),
        calendarFormat: _format,
        eventLoader: (day) => events[DateTime(day.year, day.month, day.day)] ?? [],
        headerStyle: HeaderStyle(
          formatButtonVisible: true,
          titleCentered: true,
          titleTextStyle: GoogleFonts.montserrat(fontWeight: FontWeight.w700, fontSize: 17),
          formatButtonDecoration: BoxDecoration(
            color: colors.primaryContainer,
            borderRadius: BorderRadius.circular(12),
          ),
          formatButtonTextStyle: TextStyle(color: colors.primary, fontWeight: FontWeight.w700, fontSize: 12),
          leftChevronIcon: Icon(Icons.chevron_left_rounded, color: colors.primary),
          rightChevronIcon: Icon(Icons.chevron_right_rounded, color: colors.primary),
        ),
        calendarStyle: CalendarStyle(
          todayDecoration: BoxDecoration(
            color: colors.primary.withValues(alpha: 0.1),
            shape: BoxShape.circle,
          ),
          todayTextStyle: TextStyle(color: colors.primary, fontWeight: FontWeight.w700),
          selectedDecoration: BoxDecoration(
            gradient: LinearGradient(colors: [colors.primary, colors.tertiary]),
            shape: BoxShape.circle,
          ),
          markerDecoration: const BoxDecoration(color: Colors.redAccent, shape: BoxShape.circle),
          markersMaxCount: 1,
          outsideDaysVisible: false,
        ),
        onFormatChanged: (format) => setState(() => _format = format),
        onDaySelected: (selected, focused) {
          setState(() {
            _selectedDay = DateTime(selected.year, selected.month, selected.day);
            _focusedDay = focused;
          });
        },
      ),
    ).animate().fadeIn().scale(begin: const Offset(0.98, 0.98));
  }

  Widget _buildEmptyDay(ColorScheme colors) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.calendar_today_outlined, size: 48, color: colors.outline.withValues(alpha: 0.4)),
          const SizedBox(height: 12),
          Text(
            'Enjoy your day!',
            style: GoogleFonts.montserrat(
              fontWeight: FontWeight.w600,
              color: colors.onSurfaceVariant,
            ),
          ),
        ],
      ),
    ).animate().fadeIn(delay: 200.ms);
  }

  Widget _buildStatusChip(ColorScheme colors, List<TaskItem> tasks) {
    final completed = tasks.where((t) => t.isCompleted).length;
    final allDone = completed == tasks.length && tasks.isNotEmpty;
    
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: allDone ? Colors.green : colors.secondaryContainer,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            allDone ? Icons.done_all_rounded : Icons.pending_rounded, 
            size: 14, 
            color: allDone ? Colors.white : colors.onSecondaryContainer,
          ),
          const SizedBox(width: 6),
          Text(
            allDone ? 'COMPLETED' : '$completed/${tasks.length} DONE',
            style: GoogleFonts.montserrat(
              fontWeight: FontWeight.w800,
              fontSize: 10,
              color: allDone ? Colors.white : colors.onSecondaryContainer,
            ),
          ),
        ],
      ),
    );
  }

  Map<DateTime, List<TaskItem>> _groupTasksByDate(List<TaskItem> tasks) {
    final map = <DateTime, List<TaskItem>>{};
    for (final task in tasks) {
      final date = DateTime(task.dueAt.year, task.dueAt.month, task.dueAt.day);
      map.putIfAbsent(date, () => []).add(task);
    }
    return map;
  }
}

class _CalendarTaskItem extends StatelessWidget {
  const _CalendarTaskItem({required this.task});
  final TaskItem task;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final pColor = Color(task.priorityColorValue);
    final time = DateFormat('h:mm a').format(task.dueAt);

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: colors.outlineVariant.withValues(alpha: 0.2)),
        boxShadow: [
          BoxShadow(color: pColor.withValues(alpha: 0.05), blurRadius: 10, offset: const Offset(0, 4)),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: task.categoryColor.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(task.categoryIcon, color: task.categoryColor, size: 20),
            ),
            const SizedBox(width: 14),
            Container(
              width: 6,
              height: 40,
              decoration: BoxDecoration(color: pColor, borderRadius: BorderRadius.circular(3)),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    task.title,
                    style: GoogleFonts.montserrat(
                      fontWeight: FontWeight.w700,
                      fontSize: 15,
                      decoration: task.isCompleted ? TextDecoration.lineThrough : null,
                      color: task.isCompleted ? colors.outline : colors.onSurface,
                    ),
                  ),
                  Text(time, style: TextStyle(color: colors.onSurfaceVariant, fontSize: 12)),
                ],
              ),
            ),
            if (task.isCompleted)
              const Icon(Icons.check_circle_rounded, color: Colors.green, size: 22)
            else
              IconButton(
                onPressed: () => context.read<AppState>().toggleTask(task),
                icon: Icon(Icons.radio_button_unchecked_rounded, color: colors.primary, size: 22),
              ),
          ],
        ),
      ),
    );
  }
}
