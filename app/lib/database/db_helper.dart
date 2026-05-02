import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import '../models/idea.dart';
import '../models/cluster.dart';

class DbHelper {
  static final DbHelper _instance = DbHelper._();
  static Database? _db;

  DbHelper._();
  factory DbHelper() => _instance;

  Future<Database> get db async {
    _db ??= await _init();
    return _db!;
  }

  Future<Database> _init() async {
    final path = join(await getDatabasesPath(), 'spark_vault.db');
    return openDatabase(
      path,
      version: 1,
      onCreate: _onCreate,
    );
  }

  Future<void> _onCreate(Database db, int version) async {
    await db.execute('''
      CREATE TABLE ideas (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        raw_idea         TEXT    NOT NULL,
        status           TEXT    NOT NULL DEFAULT 'draft',
        category         TEXT,
        evaluation_json  TEXT,
        research_json    TEXT,
        embedding_json   TEXT,
        synthesis_json   TEXT,
        cluster_id       INTEGER,
        created_at       INTEGER NOT NULL,
        updated_at       INTEGER NOT NULL
      )
    ''');
    await db.execute('''
      CREATE TABLE clusters (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        super_idea       TEXT,
        merge_reasoning  TEXT,
        idea_ids_json    TEXT    NOT NULL,
        created_at       INTEGER NOT NULL
      )
    ''');
  }

  // ── Ideas ──────────────────────────────────────────────────

  Future<int> insertIdea(Idea idea) async {
    final d = await db;
    return d.insert('ideas', idea.toMap());
  }

  Future<void> updateIdea(Idea idea) async {
    final d = await db;
    await d.update('ideas', idea.toMap(), where: 'id = ?', whereArgs: [idea.id]);
  }

  Future<void> deleteIdea(int id) async {
    final d = await db;
    await d.delete('ideas', where: 'id = ?', whereArgs: [id]);
  }

  Future<List<Idea>> loadAllIdeas() async {
    final d = await db;
    final rows = await d.query('ideas', orderBy: 'updated_at DESC');
    return rows.map(Idea.fromMap).toList();
  }

  Future<Idea?> loadIdea(int id) async {
    final d = await db;
    final rows = await d.query('ideas', where: 'id = ?', whereArgs: [id]);
    return rows.isEmpty ? null : Idea.fromMap(rows.first);
  }

  // ── Clusters ───────────────────────────────────────────────

  Future<int> insertCluster(Cluster cluster) async {
    final d = await db;
    return d.insert('clusters', cluster.toMap());
  }

  Future<void> updateCluster(Cluster cluster) async {
    final d = await db;
    await d.update('clusters', cluster.toMap(),
        where: 'id = ?', whereArgs: [cluster.id]);
  }

  Future<List<Cluster>> loadAllClusters() async {
    final d = await db;
    final rows = await d.query('clusters', orderBy: 'created_at DESC');
    return rows.map(Cluster.fromMap).toList();
  }

  Future<Cluster?> loadCluster(int id) async {
    final d = await db;
    final rows = await d.query('clusters', where: 'id = ?', whereArgs: [id]);
    return rows.isEmpty ? null : Cluster.fromMap(rows.first);
  }

  Future<void> deleteCluster(int id) async {
    final d = await db;
    await d.delete('clusters', where: 'id = ?', whereArgs: [id]);
    // unlink ideas from this cluster
    await d.update('ideas', {'cluster_id': null},
        where: 'cluster_id = ?', whereArgs: [id]);
  }
}
