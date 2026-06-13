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
        // Call requestPermission and poll for permission change as a fallback
        try {
          jsNotification.callMethod('requestPermission');
        } catch (_) {
          // ignore
        }
        // Poll up to ~2 seconds for permission to change from 'default'
        int attempts = 0;
        Timer.periodic(const Duration(milliseconds: 200), (t) {
          attempts++;
          try {
            final String current = jsNotification['permission'] as String;
            if (current != 'default') {
              debugPrint(
                  'WebNotifierWeb: requestPermission resolved via poll: $current');
              callback(current == 'granted');
              t.cancel();
            }
          } catch (e) {
            debugPrint('WebNotifierWeb: Poll error checking permission: $e');
          }
          if (attempts >= 10) {
            debugPrint('WebNotifierWeb: requestPermission poll timed out');
            callback(false);
            t.cancel();
          }
        });
        return;
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
        debugPrint(
            'WebNotifierWeb: Web test notification ignored because permission is $permission');
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
    debugPrint(
        'WebNotifierWeb: Cannot schedule notification in the past ($scheduledDate)');
    return;
  }

  // JS setTimeout has a max delay of 2147483647 ms (approx 24.8 days).
  // Anything larger overflows and fires immediately.
  if (delay.inMilliseconds > 2147483647) {
    debugPrint(
        'WebNotifierWeb: Delay too large for web timer ($delay). Skipping scheduling for task $id.');
    return;
  }

  debugPrint(
      'WebNotifierWeb: Scheduling task $id in ${delay.inSeconds}s (at $scheduledDate)');
  _webNotificationTimers[id] = Timer(delay, () {
    _webNotificationTimers.remove(id);
    try {
      final jsNotification = js.context['Notification'];
      if (jsNotification != null) {
        final String permission = jsNotification['permission'] as String;
        if (permission == 'granted') {
          js.context.callMethod(
              'eval', ['new Notification("$title", { body: "$body" })']);
          debugPrint(
              'WebNotifierWeb: Fired scheduled notification for task $id');
        } else {
          debugPrint(
              'WebNotifierWeb: Fired failed because permission is $permission');
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
