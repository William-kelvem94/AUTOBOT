"""
Dashboard - Módulo de Monitoramento e Métricas
==============================================

Sistema completo de dashboards e monitoramento em tempo real.
"""

from .monitor import DashboardMonitor, MetricsCollector, AlertManager, DashboardGenerator

__all__ = ['DashboardMonitor', 'MetricsCollector', 'AlertManager', 'DashboardGenerator']