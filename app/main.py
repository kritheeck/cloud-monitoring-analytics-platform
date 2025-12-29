#!/usr/bin/env python3
"""
Cloud Monitoring & Analytics Platform - Flask Application
Production-grade monitoring system with real-time metrics collection
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import psutil

# Initialize Flask App
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Prometheus Metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

cpu_usage = Gauge('system_cpu_usage_percent', 'CPU usage percentage')
memory_usage = Gauge('system_memory_usage_percent', 'Memory usage percentage')
disk_usage = Gauge('system_disk_usage_percent', 'Disk usage percentage')
active_connections = Gauge('active_connections', 'Number of active connections')

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'cloud-monitoring-platform'
    }), 200

# Metrics endpoint
@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200

# Real-time system metrics
@app.route('/api/v1/metrics/system', methods=['GET'])
def get_system_metrics():
    """Get real-time system metrics"""
    try:
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Update Prometheus gauges
        cpu_usage.set(cpu)
        memory_usage.set(memory.percent)
        disk_usage.set(disk.percent)
        
        metrics_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'cpu': {
                'usage_percent': cpu,
                'count': psutil.cpu_count(),
                'threshold': 80
            },
            'memory': {
                'usage_percent': memory.percent,
                'available_gb': round(memory.available / (1024**3), 2),
                'total_gb': round(memory.total / (1024**3), 2),
                'threshold': 85
            },
            'disk': {
                'usage_percent': disk.percent,
                'free_gb': round(disk.free / (1024**3), 2),
                'total_gb': round(disk.total / (1024**3), 2),
                'threshold': 90
            }
        }
        
        return jsonify(metrics_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Application status
@app.route('/api/v1/status', methods=['GET'])
def app_status():
    """Application status endpoint"""
    return jsonify({
        'application': 'Cloud Monitoring & Analytics Platform',
        'version': '1.0.0',
        'status': 'running',
        'environment': os.getenv('ENVIRONMENT', 'production'),
        'timestamp': datetime.utcnow().isoformat(),
        'uptime_seconds': int(time.time())
    }), 200

# Process metrics
@app.route('/api/v1/metrics/processes', methods=['GET'])
def get_process_metrics():
    """Get running processes metrics"""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_num']):
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'memory_percent': proc.info['memory_percent'],
                    'cpu': proc.info['cpu_num']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'process_count': len(processes),
            'top_processes': sorted(processes, key=lambda x: x['memory_percent'], reverse=True)[:10]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Root endpoint
@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'message': 'Cloud Monitoring & Analytics Platform',
        'api_version': 'v1',
        'endpoints': [
            '/health - Health check',
            '/metrics - Prometheus metrics',
            '/api/v1/status - Application status',
            '/api/v1/metrics/system - System metrics',
            '/api/v1/metrics/processes - Process metrics'
        ]
    }), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )
