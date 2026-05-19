import 'dart:async';
import 'dart:js' as js;
import 'package:flutter/foundation.dart';

final Map<String, Timer> _webNotificationTimers = {};

bool checkWebNotificationPermission() {
  try {
    final jsNotification = js.context['Notification'];
    if (jsNotification != null) {
      final String permission = jsNotification['permission'] as String;
      debugPrint('WebNotifierWeb: permission checked: $permission');
      return (permission == 'granted');
    }
  } catch (e) {
    debugPrint('WebNotifierWeb: Error checking permission: $e');
  }
  return false;
}

void requestWebNotificationPermission(void Function(bool) callback) {
  try {
    final jsNotification = js.context['Notification'];
    if (jsNotification != null) {
      final String permission = jsNotification['permission'] as String;
      if (permission == 'default') {
        debugPrint('WebNotifierWeb: Requesting permission...');
        final promise = jsNotification.callMethod('requestPermission');
        if (promise != null && promise is js.JsObject && promise.hasProperty('then')) {
          promise.callMethod('then', [
            js.allowInterop((result) {
              debugPrint('WebNotifierWeb: requestPermission promise resolved: $result');
              callback(result == 'granted');
            })
          ]);
        } else {
          jsNotification.callMethod('requestPermission', [
            js.allowInterop((result) {
              debugPrint('WebNotifierWeb: requestPermission callback resolved: $result');
              callback(result == 'granted');
            })
          ]);
        }
      } else {
        callback(permission == 'granted');
      }
    }
  } catch (e) {
    debugPrint('WebNotifierWeb: Error requesting permission: $e');
    callback(false);
  }
}

void sendWebTestNotification() {
  try {
    final jsNotification = js.context['Notification'];
    if (jsNotification != null) {
      final String permission = jsNotification['permission'] as String;
      if (permission == 'granted') {
        js.context.callMethod('eval', [
          'new Notification("RemindMe test notification", { body: "Sound, vibration, and delivery bar are active." })'
        ]);
        debugPrint('WebNotifierWeb: Web test notification triggered');
      } else {
        debugPrint('WebNotifierWeb: Web test notification ignored because permission is $permission');
      }
    }
  } catch (e) {
    debugPrint('WebNotifierWeb: Error sending test notification: $e');
  }
}

void scheduleWebNotification({
  required String id,
  required String title,
  required String body,
  required DateTime scheduledDate,
  required void Function() onTriggered,
}) {
  cancelWebNotification(id);

  final now = DateTime.now();
  final delay = scheduledDate.difference(now);
  if (delay.isNegative) {
    debugPrint('WebNotifierWeb: Cannot schedule notification in the past ($scheduledDate)');
    return;
  }

  debugPrint('WebNotifierWeb: Scheduling task $id in ${delay.inSeconds}s (at $scheduledDate)');
  _webNotificationTimers[id] = Timer(delay, () {
    _webNotificationTimers.remove(id);
    try {
      final jsNotification = js.context['Notification'];
      if (jsNotification != null) {
        final String permission = jsNotification['permission'] as String;
        if (permission == 'granted') {
          js.context.callMethod('eval', [
            'new Notification("$title", { body: "$body" })'
          ]);
          debugPrint('WebNotifierWeb: Fired scheduled notification for task $id');
        } else {
          debugPrint('WebNotifierWeb: Fired failed because permission is $permission');
        }
      }
    } catch (e) {
      debugPrint('WebNotifierWeb: Error firing scheduled notification: $e');
    }
    onTriggered();
  });
}

void cancelWebNotification(String id) {
  final timer = _webNotificationTimers.remove(id);
  if (timer != null) {
    timer.cancel();
    debugPrint('WebNotifierWeb: Cancelled timer for task $id');
  }
}

void cancelAllWebNotifications() {
  for (final timer in _webNotificationTimers.values) {
    timer.cancel();
  }
  _webNotificationTimers.clear();
  debugPrint('WebNotifierWeb: Cancelled all timers');
}
