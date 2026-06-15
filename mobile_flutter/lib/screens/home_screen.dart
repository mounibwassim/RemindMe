import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import 'assistant_screen.dart';
import 'audit_screen.dart';
import 'calendar_screen.dart';
import 'dashboard_screen.dart';
import 'history_screen.dart';
import 'settings_screen.dart';
import 'tasks_screen.dart';

import '../core/notification_service.dart';
import '../core/app_state.dart';
import '../models/task.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _index = 0;
  StreamSubscription<TaskItem>? _triggerSub;
  late final List<Widget> _screens;

  @override
  void initState() {
    super.initState();
    // Create screens once — do NOT use a getter, which recreates widgets
    // on every build and causes "deactivated widget" errors.
    _screens = [
      const DashboardScreen(),
      const TasksScreen(),
      const CalendarScreen(),
      const HistoryScreen(),
      AssistantScreen(onGoHome: () => setState(() => _index = 0)),
      const AuditScreen(),
      const SettingsScreen(),
    ];
    _requestNotificationPermission();

    final state = context.read<AppState>();
    _triggerSub = state.onTaskTriggered.listen((task) {
      if (mounted) {
        _showInAppNotificationDialog(task);
      }
    });
  }

  @override
  void dispose() {
    _triggerSub?.cancel();
    super.dispose();
  }

  Future<void> _requestNotificationPermission() async {
    await NotificationService().requestPermissions();
  }

  void _showInAppNotificationDialog(TaskItem task) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) {
        final colors = Theme.of(context).colorScheme;
        return AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
          title: Row(
            children: [
              Icon(Icons.alarm_on_rounded, color: colors.primary, size: 28),
              const SizedBox(width: 12),
              const Text('Task Alarm!'),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                task.title,
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
              ),
              if (task.description.isNotEmpty) ...[
                const SizedBox(height: 12),
                Text(
                  task.description,
                  style: TextStyle(color: colors.onSurfaceVariant),
                ),
              ],
            ],
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.pop(ctx);
              },
              child: const Text('Dismiss'),
            ),
            FilledButton(
              onPressed: () async {
                Navigator.pop(ctx);
                await context.read<AppState>().completeTask(task);
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('Task "${task.title}" completed!'),
                      behavior: SnackBarBehavior.floating,
                    ),
                  );
                }
              },
              child: const Text('Complete Task'),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    return Scaffold(
      appBar: _index == 0 ? null : AppBar(
        title: Text(
          _index == 1 ? 'Tasks' :
          _index == 2 ? 'Calendar' :
          _index == 3 ? 'History' :
          _index == 4 ? 'AI Assistant' :
          _index == 5 ? 'Audit Logs' : 'Settings',
          style: GoogleFonts.montserrat(
            fontWeight: FontWeight.w800,
            fontSize: 18,
            letterSpacing: -0.5,
          ),
        ),
        centerTitle: true,
        actions: const [],
      ),
      body: Column(
        children: [

          Expanded(
            child: Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: Theme.of(context).brightness == Brightness.dark
                      ? [const Color(0xFF0F172A), const Color(0xFF111827)]
                      : [const Color(0xFFF1F5F9), const Color(0xFFE2E8F0)],
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                ),
              ),
              child: Stack(
                children: [
                  // ── Decorative Background Elements ────────────────────────
                  Positioned(
                    top: -100,
                    right: -50,
                    child: Container(
                      width: 300,
                      height: 300,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: const Color(0xFF00C2FF).withValues(alpha: 0.1),
                      ),
                    ),
                  ),
                  Positioned(
                    bottom: 100,
                    left: -80,
                    child: Container(
                      width: 250,
                      height: 250,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: const Color(0xFF38BDF8).withValues(alpha: 0.08),
                      ),
                    ),
                  ),
                  
                  // ── Main Content ──────────────────────────────────────────
                  AnimatedSwitcher(
                    duration: const Duration(milliseconds: 300),
                    child: _screens[_index],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
      bottomNavigationBar: NavigationBarTheme(
        data: NavigationBarThemeData(
          height: 60, // Slimmer profile
          labelTextStyle: WidgetStateProperty.all(
            const TextStyle(fontSize: 9, fontWeight: FontWeight.w600, letterSpacing: -0.2),
          ),
          iconTheme: WidgetStateProperty.all(const IconThemeData(size: 20)),
        ),
        child: NavigationBar(
          selectedIndex: _index,
          labelBehavior: NavigationDestinationLabelBehavior.alwaysShow, // Show all since we made them small
          onDestinationSelected: (value) => setState(() => _index = value),
          destinations: const [
            NavigationDestination(
              icon: Icon(Icons.dashboard_outlined),
              selectedIcon: Icon(Icons.dashboard_rounded),
              label: 'Home', // Shorter than 'Dashboard'
            ),
            NavigationDestination(
              icon: Icon(Icons.checklist_outlined),
              selectedIcon: Icon(Icons.checklist_rounded),
              label: 'Tasks',
            ),
            NavigationDestination(
              icon: Icon(Icons.calendar_month_outlined),
              selectedIcon: Icon(Icons.calendar_month_rounded),
              label: 'Calendar',
            ),
            NavigationDestination(
              icon: Icon(Icons.history_outlined),
              selectedIcon: Icon(Icons.history_rounded),
              label: 'History',
            ),
            NavigationDestination(
              icon: Icon(Icons.auto_awesome_outlined),
              selectedIcon: Icon(Icons.auto_awesome_rounded),
              label: 'AI',
            ),
            NavigationDestination(
              icon: Icon(Icons.analytics_outlined),
              selectedIcon: Icon(Icons.analytics_rounded),
              label: 'Audit',
            ),
            NavigationDestination(
              icon: Icon(Icons.settings_outlined),
              selectedIcon: Icon(Icons.settings_rounded),
              label: 'Settings',
            ),
          ],
        ),
      ),
    );
  }
}
