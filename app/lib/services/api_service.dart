import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/idea.dart';

class ApiException implements Exception {
  final String message;
  final int?   statusCode;
  ApiException(this.message, {this.statusCode});
  @override String toString() => message;
}

class ApiService {
  static const _defaultUrl = 'https://idea-engine-zbno.onrender.com';
  static const _prefKey    = 'backend_url';

  Future<String> get baseUrl async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_prefKey) ?? _defaultUrl;
  }

  Future<void> setBaseUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_prefKey, url.trimRight().replaceAll(RegExp(r'/$'), ''));
  }

  /// Submits idea for processing, then polls until done. Returns result map.
  /// Uses submit+poll to avoid mobile network timeouts on 2-minute+ requests.
  Future<Map<String, dynamic>> processIdea({
    required String rawIdea,
    required List<Idea> pastIdeas,
    String depth    = 'balanced',
    String? category,
  }) async {
    final url = await baseUrl;

    final body = jsonEncode({
      'raw_idea':   rawIdea,
      'past_ideas': pastIdeas.map((i) => i.toApiShape()).toList(),
      'depth':      depth,
      if (category != null) 'category': category,
    });

    // Step 1: submit — returns job_id immediately
    final submitRes = await http.post(
      Uri.parse('$url/process-idea'),
      headers: {'Content-Type': 'application/json'},
      body: body,
    ).timeout(
      const Duration(seconds: 30),
      onTimeout: () => throw ApiException('Submit timed out'),
    );

    if (submitRes.statusCode != 200) {
      String detail = 'Server error ${submitRes.statusCode}';
      try { detail = jsonDecode(submitRes.body)['detail'] ?? detail; } catch (_) {}
      throw ApiException(detail, statusCode: submitRes.statusCode);
    }

    final jobId = jsonDecode(submitRes.body)['job_id'] as String;

    // Step 2: poll every 5s until completed or failed (max 10 min)
    final deadline = DateTime.now().add(const Duration(minutes: 10));
    while (DateTime.now().isBefore(deadline)) {
      await Future.delayed(const Duration(seconds: 5));

      final statusRes = await http.get(
        Uri.parse('$url/idea-status/$jobId'),
      ).timeout(
        const Duration(seconds: 15),
        onTimeout: () => throw ApiException('Status check timed out'),
      );

      if (statusRes.statusCode == 200) {
        final data = Map<String, dynamic>.from(jsonDecode(statusRes.body));
        if (data['status'] == 'completed') return data;
        if (data['status'] == 'failed') {
          throw ApiException(data['error'] as String? ?? 'Processing failed');
        }
        // still processing — keep polling
      }
    }

    throw ApiException('Processing timed out after 10 minutes');
  }

  /// Health check — returns true if backend is reachable.
  Future<bool> ping() async {
    try {
      final url = await baseUrl;
      final res = await http.get(Uri.parse('$url/')).timeout(const Duration(seconds: 10));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }
}
