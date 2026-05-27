import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:timezone/data/latest_all.dart' as tz;
import 'package:timezone/timezone.dart' as tz;

import 'app.dart';
import 'core/app_state.dart';
import 'core/api_client.dart';
import 'core/notification_service.dart';

@pragma('vm:entry-point')
void notificationTapBackground(NotificationResponse notificationResponse) async {
  final actionId = notificationResponse.actionId;
  final payload = notificationResponse.payload;

  if (payload != null && payload.startsWith('task:') && actionId != null) {
    final taskId = payload.substring(5);
    final prefs = await SharedPreferences.getInstance();
    final session = prefs.getString('session_id');

    if (session != null) {
      const explicitUrl = String.fromEnvironment('API_URL');
      final detectedUrl = explicitUrl.isNotEmpty
          ? explicitUrl
          : (kReleaseMode ? 'https://remindme-backend.onrender.com' : 'http://10.0.2.2:8000');
      final api = ApiClient(baseUrl: detectedUrl);
      api.setSession(session);

      try {
        if (actionId == 'snooze') {
          await api.snoozeTask(taskId, 15);
          final tasks = await api.getTasks();
          final updatedTask = tasks.firstWhere((t) => t.id == taskId);
          final ns = NotificationService();
          await ns.init();
          await ns.scheduleNotification(
            id: updatedTask.id,
            title: updatedTask.title,
            body: 'Alarm: ${updatedTask.title} is due now!',
            scheduledDate: updatedTask.dueAt,
          );
        } else if (actionId == 'complete') {
          await api.completeTask(taskId);
        }
      } catch (e) {
        debugPrint('Background notification action failed: $e');
      }
    }
  }
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  tz.initializeTimeZones();
  
  runApp(
    ChangeNotifierProvider(
      create: (_) => AppState(),
      child: const RemindMeApp(),
    ),
  );
}
