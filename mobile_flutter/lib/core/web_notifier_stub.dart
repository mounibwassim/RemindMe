import 'package:flutter/foundation.dart';

bool checkWebNotificationPermission() {
  return false;
}

void requestWebNotificationPermission(void Function(bool) callback) {
  callback(false);
}

void sendWebTestNotification() {
  debugPrint('WebNotifierStub: sendWebTestNotification ignored on this platform');
}

void scheduleWebNotification({
  required String id,
  required String title,
  required String body,
  required DateTime scheduledDate,
  required void Function() onTriggered,
}) {
  debugPrint('WebNotifierStub: scheduleWebNotification ignored on this platform');
}

void cancelWebNotification(String id) {
  debugPrint('WebNotifierStub: cancelWebNotification ignored on this platform');
}

void cancelAllWebNotifications() {
  debugPrint('WebNotifierStub: cancelAllWebNotifications ignored on this platform');
}

void showWebNotification(String title, String body) {
  debugPrint('WebNotifierStub: showWebNotification ignored on this platform');
}
