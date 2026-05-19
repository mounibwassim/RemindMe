class Session {
  const Session({
    required this.sessionId,
    required this.username,
    required this.email,
  });

  final String sessionId;
  final String username;
  final String email;

  factory Session.fromJson(Map<String, dynamic> json) {
    return Session(
      sessionId: json['session_id'] as String,
      username: json['username'] as String,
      email: json['email'] as String,
    );
  }
}
