import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/ideas_provider.dart';
import '../models/idea.dart';
import '../models/cluster.dart';
import '../theme/app_theme.dart';
import '../widgets/note_card.dart';
import 'note_screen.dart';
import 'settings_screen.dart';
import 'cluster_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabs;
  final _searchCtrl = TextEditingController();
  String _query = '';

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 2, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<IdeasProvider>().load();
    });
  }

  @override
  void dispose() {
    _tabs.dispose();
    _searchCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bg,
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(),
            _buildSearch(),
            _buildTabs(),
            Expanded(child: TabBarView(
              controller: _tabs,
              children: [_IdeasTab(query: _query), const _ClustersTab()],
            )),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _newNote,
        child: const Icon(Icons.add, size: 28),
      ),
    );
  }

  Widget _buildHeader() => Padding(
    padding: const EdgeInsets.fromLTRB(20, 20, 16, 4),
    child: Row(
      children: [
        const Text(
          'Spark Vault',
          style: TextStyle(
            color: AppColors.text,
            fontSize: 24,
            fontWeight: FontWeight.w600,
            letterSpacing: -0.5,
          ),
        ),
        const Spacer(),
        IconButton(
          icon: const Icon(Icons.settings_outlined, color: AppColors.textMuted),
          onPressed: () => Navigator.push(context,
              MaterialPageRoute(builder: (_) => const SettingsScreen())),
        ),
      ],
    ),
  );

  Widget _buildSearch() => Padding(
    padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
    child: Container(
      height: 40,
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.border, width: 0.5),
      ),
      child: Row(
        children: [
          const SizedBox(width: 12),
          const Icon(Icons.search, color: AppColors.textDim, size: 18),
          const SizedBox(width: 8),
          Expanded(
            child: TextField(
              controller: _searchCtrl,
              style: const TextStyle(color: AppColors.text, fontSize: 14),
              decoration: const InputDecoration(
                hintText: 'Search notes…',
                hintStyle: TextStyle(color: AppColors.textDim, fontSize: 14),
                border: InputBorder.none,
                isDense: true,
              ),
              onChanged: (v) => setState(() => _query = v),
            ),
          ),
          if (_query.isNotEmpty)
            GestureDetector(
              onTap: () { _searchCtrl.clear(); setState(() => _query = ''); },
              child: const Padding(
                padding: EdgeInsets.symmetric(horizontal: 10),
                child: Icon(Icons.close, color: AppColors.textDim, size: 16),
              ),
            ),
        ],
      ),
    ),
  );

  Widget _buildTabs() => TabBar(
    controller: _tabs,
    tabs: const [Tab(text: 'Notes'), Tab(text: 'Clusters')],
    labelColor: AppColors.amber,
    unselectedLabelColor: AppColors.textMuted,
    indicatorColor: AppColors.amber,
    indicatorSize: TabBarIndicatorSize.label,
    dividerColor: AppColors.border,
  );

  Future<void> _newNote() async {
    final provider = context.read<IdeasProvider>();
    final idea = await provider.createIdea('');
    if (!mounted) return;
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => NoteScreen(idea: idea, isNew: true)),
    );
  }
}

// ── Ideas tab ────────────────────────────────────────────────

class _IdeasTab extends StatelessWidget {
  final String query;
  const _IdeasTab({required this.query});

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<IdeasProvider>();
    final ideas = query.isEmpty
        ? provider.ideas
        : provider.ideas.where(
            (i) => i.rawIdea.toLowerCase().contains(query.toLowerCase())).toList();

    if (provider.loading) {
      return const Center(child: CircularProgressIndicator(color: AppColors.amber));
    }
    if (ideas.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.lightbulb_outline, color: AppColors.textDim, size: 48),
            const SizedBox(height: 16),
            Text(
              query.isEmpty ? 'No notes yet\nTap + to start' : 'No results',
              textAlign: TextAlign.center,
              style: const TextStyle(color: AppColors.textDim, fontSize: 15, height: 1.6),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.only(top: 8, bottom: 100),
      itemCount: ideas.length,
      itemBuilder: (ctx, i) {
        final idea = ideas[i];
        return NoteCard(
          idea: idea,
          onTap: () => Navigator.push(ctx,
              MaterialPageRoute(builder: (_) => NoteScreen(idea: idea))),
          onDelete: () => _confirmDelete(ctx, idea),
        );
      },
    );
  }

  void _confirmDelete(BuildContext context, Idea idea) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.surface2,
        title: const Text('Delete note?', style: TextStyle(color: AppColors.text)),
        content: Text(
          idea.title,
          style: const TextStyle(color: AppColors.textMuted),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel', style: TextStyle(color: AppColors.textMuted)),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(ctx);
              context.read<IdeasProvider>().deleteIdea(idea.id!);
            },
            child: const Text('Delete', style: TextStyle(color: AppColors.red)),
          ),
        ],
      ),
    );
  }
}

// ── Clusters tab ─────────────────────────────────────────────

class _ClustersTab extends StatelessWidget {
  const _ClustersTab();

  @override
  Widget build(BuildContext context) {
    final provider  = context.watch<IdeasProvider>();
    final clusters  = provider.clusters;

    if (clusters.isEmpty) {
      return const Center(
        child: Text(
          'No clusters yet.\nAnalyze more notes to find connections.',
          textAlign: TextAlign.center,
          style: TextStyle(color: AppColors.textDim, fontSize: 14, height: 1.6),
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.only(top: 8, bottom: 100),
      itemCount: clusters.length,
      itemBuilder: (ctx, i) {
        final cluster = clusters[i];
        final clusterIdeas = provider.ideasInCluster(cluster);
        return _ClusterCard(
          cluster: cluster,
          ideas: clusterIdeas,
          onTap: () => Navigator.push(ctx, MaterialPageRoute(
            builder: (_) => ClusterScreen(cluster: cluster, ideas: clusterIdeas),
          )),
        );
      },
    );
  }
}

class _ClusterCard extends StatelessWidget {
  final Cluster      cluster;
  final List<Idea>   ideas;
  final VoidCallback onTap;
  const _ClusterCard({required this.cluster, required this.ideas, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 5),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.hub_outlined, color: AppColors.amber, size: 14),
              const SizedBox(width: 6),
              Text(
                'Cluster #${cluster.id}  ·  ${ideas.length} notes',
                style: const TextStyle(
                  color: AppColors.amber, fontSize: 11, letterSpacing: 0.3,
                ),
              ),
            ],
          ),
          if (cluster.superIdea != null) ...[
            const SizedBox(height: 10),
            Text(
              cluster.superIdea!,
              style: const TextStyle(
                color: AppColors.text, fontSize: 14, height: 1.5,
              ),
            ),
          ],
          if (ideas.isNotEmpty) ...[
            const SizedBox(height: 10),
            Wrap(
              spacing: 6, runSpacing: 4,
              children: ideas.map((i) => Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: AppColors.surface2,
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: AppColors.border, width: 0.5),
                ),
                child: Text(
                  i.title,
                  style: const TextStyle(color: AppColors.textMuted, fontSize: 11),
                ),
              )).toList(),
            ),
          ],
        ],
      ),
    ));
  }
}
