import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/ideas_provider.dart';
import '../theme/app_theme.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});
  @override State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late TextEditingController _urlCtrl;
  bool _pinging  = false;
  bool? _pingOk;

  @override
  void initState() {
    super.initState();
    _urlCtrl = TextEditingController();
    _loadUrl();
  }

  Future<void> _loadUrl() async {
    final url = await context.read<IdeasProvider>().getBackendUrl();
    if (mounted) _urlCtrl.text = url;
  }

  @override
  void dispose() {
    _urlCtrl.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    await context.read<IdeasProvider>().setBackendUrl(_urlCtrl.text.trim());
    if (mounted) _showSnack('Saved.');
  }

  Future<void> _ping() async {
    await context.read<IdeasProvider>().setBackendUrl(_urlCtrl.text.trim());
    setState(() { _pinging = true; _pingOk = null; });
    final ok = await context.read<IdeasProvider>().pingBackend();
    if (mounted) setState(() { _pinging = false; _pingOk = ok; });
  }

  void _showSnack(String msg) => ScaffoldMessenger.of(context)
      .showSnackBar(SnackBar(
        content: Text(msg),
        backgroundColor: AppColors.surface2,
        behavior: SnackBarBehavior.floating,
      ));

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bg,
      appBar: AppBar(
        title: const Text('Settings'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, size: 18, color: AppColors.textMuted),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const Text('BACKEND', style: TextStyle(
            color: AppColors.amber, fontSize: 10,
            fontWeight: FontWeight.w600, letterSpacing: 1.0,
          )),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.border, width: 0.5),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Backend URL', style: TextStyle(
                  color: AppColors.textDim, fontSize: 11,
                )),
                const SizedBox(height: 6),
                TextField(
                  controller: _urlCtrl,
                  style: const TextStyle(color: AppColors.text, fontSize: 14),
                  decoration: InputDecoration(
                    hintText: 'https://your-app.onrender.com',
                    hintStyle: const TextStyle(color: AppColors.textDim),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                      borderSide: const BorderSide(color: AppColors.border, width: 0.5),
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                      borderSide: const BorderSide(color: AppColors.border, width: 0.5),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                      borderSide: const BorderSide(color: AppColors.amber, width: 1),
                    ),
                    contentPadding: const EdgeInsets.symmetric(
                        horizontal: 12, vertical: 10),
                  ),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    _ActionButton(label: 'Save', onTap: _save),
                    const SizedBox(width: 8),
                    _ActionButton(
                      label: _pinging ? 'Pinging…' : 'Test connection',
                      onTap: _pinging ? null : _ping,
                    ),
                    if (_pingOk != null) ...[
                      const SizedBox(width: 10),
                      Icon(
                        _pingOk! ? Icons.check_circle_outline : Icons.error_outline,
                        color: _pingOk! ? AppColors.green : AppColors.red,
                        size: 18,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        _pingOk! ? 'Online' : 'Unreachable',
                        style: TextStyle(
                          color: _pingOk! ? AppColors.green : AppColors.red,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          const Text('ABOUT', style: TextStyle(
            color: AppColors.amber, fontSize: 10,
            fontWeight: FontWeight.w600, letterSpacing: 1.0,
          )),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.border, width: 0.5),
            ),
            child: const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _InfoRow(label: 'App', value: 'Spark Vault'),
                _InfoRow(label: 'Version', value: '1.0.3'),
                _InfoRow(label: 'Storage', value: 'Local SQLite (on device)'),
                _InfoRow(label: 'Processing', value: 'Render backend (cloud)'),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ActionButton extends StatelessWidget {
  final String   label;
  final VoidCallback? onTap;
  const _ActionButton({required this.label, this.onTap});

  @override Widget build(BuildContext context) => GestureDetector(
    onTap: onTap,
    child: Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
      decoration: BoxDecoration(
        color: onTap == null ? AppColors.surface2 : AppColors.amberDim,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: onTap == null ? AppColors.border : AppColors.amber.withOpacity(0.4),
          width: 0.5,
        ),
      ),
      child: Text(label, style: TextStyle(
        color: onTap == null ? AppColors.textDim : AppColors.amber,
        fontSize: 12,
        fontWeight: FontWeight.w500,
      )),
    ),
  );
}

class _InfoRow extends StatelessWidget {
  final String label;
  final String value;
  const _InfoRow({required this.label, required this.value});

  @override Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 8),
    child: Row(
      children: [
        SizedBox(
          width: 90,
          child: Text(label, style: const TextStyle(
            color: AppColors.textDim, fontSize: 12,
          )),
        ),
        Text(value, style: const TextStyle(
          color: AppColors.textMuted, fontSize: 12,
        )),
      ],
    ),
  );
}
