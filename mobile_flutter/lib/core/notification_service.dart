import 'dart:ui';

import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:timezone/data/latest_all.dart' as tz;
import 'package:timezone/timezone.dart' as tz;
import 'web_notifier_stub.dart' if (dart.library.js) 'web_notifier_web.dart'
    as web_notifier;
import '../main.dart';

typedef NotificationTapHandler = void Function(String? payload);

class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  static const String taskChannelId = 'remindme_task_alarms';
  static const String taskChannelName = 'Task alarms';
  static const String taskChannelDescription =
      'Exact RemindMe alerts for task deadlines';

  final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();

  static final Int64List _vibrationPattern =
      Int64List.fromList([0, 700, 250, 700, 250, 1000]);

  static final AndroidNotificationDetails _androidAlarmDetails =
      AndroidNotificationDetails(
    taskChannelId,
    taskChannelName,
    channelDescription: taskChannelDescription,
    importance: Importance.max,
    priority: Priority.max,
    category: AndroidNotificationCategory.alarm,
    visibility: NotificationVisibility.public,
    fullScreenIntent: true,
    playSound: true,
    enableVibration: true,
    vibrationPattern: _vibrationPattern,
    enableLights: true,
    ledColor: const Color(0xFF2563EB),
    ledOnMs: 1000,
    ledOffMs: 500,
    showWhen: true,
    autoCancel: true,
    ticker: 'RemindMe task alert',
    actions: <AndroidNotificationAction>[
      const AndroidNotificationAction(
        'snooze',
        'Snooze (15m)',
        showsUserInterface: true,
      ),
      const AndroidNotificationAction(
        'complete',
        'Complete',
        showsUserInterface: true,
      ),
    ],
  );

  Future<void> init({NotificationTapHandler? onTap}) async {
    tz.initializeTimeZones();
    try {
      final String timeZoneName = DateTime.now().timeZoneName;
      tz.setLocalLocation(tz.getLocation(timeZoneName));
    } catch (_) {
      tz.setLocalLocation(tz.UTC);
    }

    if (kIsWeb) {
      await checkPermissions();
      return;
    }

    const androidInit = AndroidInitializationSettings('@mipmap/ic_launcher');
    const initSettings = InitializationSettings(android: androidInit);

    await _plugin.initialize(
      initSettings,
      onDidReceiveNotificationResponse: (details) {
        onTap?.call(details.payload);
      },
      onDidReceiveBackgroundNotificationResponse: notificationTapBackground,
    );

    final androidPlugin = _plugin.resolvePlatformSpecificImplementation<
        AndroidFlutterLocalNotificationsPlugin>();

    await androidPlugin?.createNotificationChannel(
      AndroidNotificationChannel(
        taskChannelId,
        taskChannelName,
        description: taskChannelDescription,
        importance: Importance.max,
        playSound: true,
        enableVibration: true,
        vibrationPattern: _vibrationPattern,
        ledColor: const Color(0xFF2563EB),
        enableLights: true,
      ),
    );
    await checkPermissions();
  }

  bool _isPermissionGranted = false;
  bool get isPermissionGranted => _isPermissionGranted;

  Future<void> checkPermissions() async {
    if (kIsWeb) {
      _isPermissionGranted = web_notifier.checkWebNotificationPermission();
      return;
    }

    final androidPlugin = _plugin.resolvePlatformSpecificImplementation<
        AndroidFlutterLocalNotificationsPlugin>();
    if (androidPlugin != null) {
      _isPermissionGranted =
          await androidPlugin.areNotificationsEnabled() ?? false;
    }
  }

  Future<void> requestPermissions() async {
    if (kIsWeb) {
      web_notifier.requestWebNotificationPermission((granted) {
        _isPermissionGranted = granted;
      });
      return;
    }

    final androidPlugin = _plugin.resolvePlatformSpecificImplementation<
        AndroidFlutterLocalNotificationsPlugin>();
    if (androidPlugin != null) {
      final granted = await androidPlugin.requestNotificationsPermission();
      _isPermissionGranted = granted ?? false;
      await androidPlugin.requestExactAlarmsPermission();
    }
  }

  Future<void> scheduleNotification({
    required String id,
    required String title,
    required String body,
    required DateTime scheduledDate,
    VoidCallback? onTriggered,
  }) async {
    if (kIsWeb) {
      web_notifier.scheduleWebNotification(
        id: id,
        title: title,
        body: body,
        scheduledDate: scheduledDate,
        onTriggered: onTriggered ?? () {},
      );
      return;
    }
    final intId = id.hashCode & 0x7FFFFFFF;
    if (scheduledDate.isBefore(DateTime.now())) return;
    try {
      await _plugin.zonedSchedule(
        intId,
        title,
        body,
        tz.TZDateTime.from(scheduledDate, tz.local),
        NotificationDetails(android: _androidAlarmDetails),
        androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
        uiLocalNotificationDateInterpretation:
            UILocalNotificationDateInterpretation.absoluteTime,
        payload: 'task:$id',
      );
      debugPrint('Notification scheduled: ID $id at $scheduledDate');
    } catch (e) {
      debugPrint('Notification scheduling failed: $e');
    }
  }

  Future<void> cancelNotification(String id) async {
    if (kIsWeb) {
      web_notifier.cancelWebNotification(id);
      return;
    }
    await _plugin.cancel(id.hashCode & 0x7FFFFFFF);
    debugPrint('Notification cancelled: ID $id');
  }

  Future<void> sendTestNotification() async {
    if (kIsWeb) {
      web_notifier.sendWebTestNotification();
      return;
    }

    await _plugin.show(
      900001,
      'RemindMe test notification',
      'Sound, vibration, and delivery bar are active.',
      NotificationDetails(android: _androidAlarmDetails),
      payload: 'test',
    );
  }

  Future<void> cancelAll() async {
    if (kIsWeb) {
      web_notifier.cancelAllWebNotifications();
      return;
    }
    await _plugin.cancelAll();
  }
}
