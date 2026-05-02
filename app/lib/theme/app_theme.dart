import 'package:flutter/material.dart';

class AppColors {
  static const bg         = Color(0xFF0C0C0B);
  static const surface    = Color(0xFF141412);
  static const surface2   = Color(0xFF1C1C19);
  static const border     = Color(0x12FFFFFF);
  static const border2    = Color(0x26FFFFFF);
  static const amber      = Color(0xFFD4922A);
  static const amberDim   = Color(0x1FD4922A);
  static const text       = Color(0xFFE8E4DC);
  static const textMuted  = Color(0xFFB0A898);
  static const textDim    = Color(0xFF6B6760);
  static const green      = Color(0xFF4CAF7A);
  static const greenDim   = Color(0x1A4CAF7A);
  static const red        = Color(0xFFC0524A);
  static const redDim     = Color(0x1AC0524A);
}

class AppTheme {
  static ThemeData get dark => ThemeData(
    brightness: Brightness.dark,
    scaffoldBackgroundColor: AppColors.bg,
    colorScheme: const ColorScheme.dark(
      surface: AppColors.surface,
      primary: AppColors.amber,
      onPrimary: AppColors.bg,
      onSurface: AppColors.text,
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: AppColors.bg,
      foregroundColor: AppColors.text,
      elevation: 0,
      scrolledUnderElevation: 0,
      centerTitle: false,
      titleTextStyle: TextStyle(
        fontFamily: 'serif',
        fontSize: 20,
        fontWeight: FontWeight.w600,
        color: AppColors.text,
        letterSpacing: -0.3,
      ),
    ),
    tabBarTheme: const TabBarThemeData(
      labelColor: AppColors.amber,
      unselectedLabelColor: AppColors.textMuted,
      indicatorColor: AppColors.amber,
      indicatorSize: TabBarIndicatorSize.label,
      labelStyle: TextStyle(fontSize: 13, fontWeight: FontWeight.w500, letterSpacing: 0.3),
      unselectedLabelStyle: TextStyle(fontSize: 13, fontWeight: FontWeight.w400),
    ),
    inputDecorationTheme: const InputDecorationTheme(
      border: InputBorder.none,
      hintStyle: TextStyle(color: AppColors.textDim),
    ),
    floatingActionButtonTheme: const FloatingActionButtonThemeData(
      backgroundColor: AppColors.amber,
      foregroundColor: AppColors.bg,
      elevation: 4,
    ),
    dividerTheme: const DividerThemeData(
      color: AppColors.border,
      thickness: 0.5,
    ),
    textTheme: const TextTheme(
      bodyLarge:  TextStyle(color: AppColors.text,      fontSize: 15, height: 1.6),
      bodyMedium: TextStyle(color: AppColors.text,      fontSize: 14, height: 1.6),
      bodySmall:  TextStyle(color: AppColors.textMuted, fontSize: 12, height: 1.5),
      labelSmall: TextStyle(color: AppColors.textDim,   fontSize: 11),
    ),
  );
}
