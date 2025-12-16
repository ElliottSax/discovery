"""
Integration Tests for Phase 1 Pattern Discovery Improvements

Tests all new pattern discovery methods:
1. Matrix Profile - Motif discovery
2. Multi-Resolution Wavelet Analysis
3. SAX Pattern Library
4. Multi-Scale Pattern Mining
5. Dynamic Network Evolution
6. Unified Pattern Library

Author: Claude
"""

import numpy as np
import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.patterns.matrix_profile import MatrixProfileAnalyzer
from analysis.patterns.motif_discovery import MotifDiscoveryEngine, MotifLibrary
from analysis.advanced.wavelet import MultiResolutionWaveletAnalyzer, quick_multiscale_analysis
from analysis.patterns.sax_patterns import SAXTransformer, SAXPatternMiner, quick_sax_analysis
from analysis.patterns.multiscale_patterns import MultiScalePatternMiner, analyze_politician_multiscale
from analysis.patterns.pattern_library import IntegratedPatternDiscovery
from analysis.network.temporal_networks import (
    BurstyEventDetector,
    NetworkEntropyAnalyzer,
    InfluencePropagationAnalyzer,
    DynamicCommunityDetector
)


def generate_test_time_series(length: int = 200, add_patterns: bool = True) -> np.ndarray:
    """Generate synthetic time series with patterns for testing."""
    # Base signal
    time = np.arange(length)
    signal = np.zeros(length)

    if add_patterns:
        # Add some patterns
        # Pattern 1: Weekly cycle (period 7)
        signal += 2 * np.sin(2 * np.pi * time / 7)

        # Pattern 2: Monthly cycle (period 30)
        signal += 1.5 * np.sin(2 * np.pi * time / 30)

        # Add some noise
        signal += np.random.normal(0, 0.5, length)

        # Add a few anomalies
        anomaly_indices = [50, 100, 150]
        for idx in anomaly_indices:
            if idx < length:
                signal[idx] += 5

    else:
        # Just noise
        signal = np.random.normal(0, 1, length)

    return signal


def test_matrix_profile():
    """Test Matrix Profile pattern discovery."""
    print("\n" + "=" * 60)
    print("TEST 1: Matrix Profile Pattern Discovery")
    print("=" * 60)

    # Generate test data
    ts = generate_test_time_series(200)

    try:
        # Initialize analyzer
        analyzer = MatrixProfileAnalyzer(window_size=20)

        # Discover motifs
        result = analyzer.discover_motifs(ts, k_motifs=3)

        print(f"✓ Discovered {result['num_motifs']} motifs")
        print(f"  Method: {result['discovery_method']}")

        for motif in result['motifs'][:3]:
            print(f"  - Motif {motif['motif_id']}: Similarity={motif['similarity']:.3f}")

        # Discover discords (anomalies)
        discord_result = analyzer.find_discords(ts, k_discords=3)

        print(f"✓ Discovered {discord_result['num_discords']} discords (anomalies)")

        return True

    except Exception as e:
        print(f"✗ Matrix Profile test failed: {e}")
        return False


def test_multiscale_wavelet():
    """Test Multi-Resolution Wavelet Analysis."""
    print("\n" + "=" * 60)
    print("TEST 2: Multi-Resolution Wavelet Analysis")
    print("=" * 60)

    # Generate test data
    ts = generate_test_time_series(256)  # Power of 2 for wavelets

    try:
        # Quick analysis
        result = quick_multiscale_analysis(ts)

        print(f"✓ Decomposition completed")
        print(f"  Max level: {result['max_level']}")
        print(f"  Reconstruction error: {result['reconstruction_error']:.6f}")

        # Cross-scale correlations
        correlations = result['cross_scale_correlations']
        print(f"✓ Cross-scale analysis:")
        print(f"  Significant correlations: {correlations['n_significant']}")

        # Multiscale anomalies
        anomalies = result['anomalies']
        print(f"✓ Anomaly detection:")
        print(f"  Multiscale anomalies: {anomalies['n_multiscale']}")

        return True

    except Exception as e:
        print(f"✗ Wavelet test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sax_patterns():
    """Test SAX Pattern Library."""
    print("\n" + "=" * 60)
    print("TEST 3: SAX Pattern Library")
    print("=" * 60)

    # Generate test data
    ts = generate_test_time_series(150)

    try:
        # Quick SAX analysis
        result = quick_sax_analysis(ts, word_size=10, alphabet_size=5)

        print(f"✓ SAX transformation completed")
        print(f"  SAX string: {result['sax_string']}")
        print(f"  Word size: {result['word_size']}")
        print(f"  Alphabet size: {result['alphabet_size']}")

        # Pattern mining
        stats = result['statistics']
        print(f"✓ Pattern mining:")
        print(f"  Unique patterns: {stats['n_unique_patterns']}")
        print(f"  Frequent patterns: {stats['n_frequent']}")

        # Test distance calculation
        transformer = SAXTransformer(word_size=10, alphabet_size=5)
        ts2 = generate_test_time_series(150)
        sax2 = transformer.transform(ts2)

        distance = transformer.distance(result['sax_string'], sax2)
        print(f"✓ Distance calculation: {distance:.3f}")

        return True

    except Exception as e:
        print(f"✗ SAX test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiscale_mining():
    """Test Multi-Scale Pattern Mining."""
    print("\n" + "=" * 60)
    print("TEST 4: Multi-Scale Pattern Mining")
    print("=" * 60)

    # Generate test data
    ts = generate_test_time_series(300)

    try:
        # Initialize miner
        miner = MultiScalePatternMiner(scales=[7, 14, 30])

        # Discover patterns
        result = miner.discover_multiscale_patterns(
            ts,
            use_wavelet=False,  # Skip wavelet for speed
            use_matrix_profile=True
        )

        summary = result['summary']
        print(f"✓ Multi-scale analysis completed")
        print(f"  Scales analyzed: {summary['scales_analyzed']}")
        print(f"  Matrix profile patterns: {summary['n_matrix_profile_patterns']}")
        print(f"  Scale-invariant patterns: {summary['n_scale_invariant']}")

        # Hierarchical structure
        hierarchy = result['hierarchy']
        print(f"✓ Hierarchical analysis:")
        print(f"  Hierarchy levels: {hierarchy['hierarchy_levels']}")
        print(f"  Cross-scale relationships: {hierarchy['n_relationships']}")

        return True

    except Exception as e:
        print(f"✗ Multi-scale mining test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integrated_discovery():
    """Test Integrated Pattern Discovery."""
    print("\n" + "=" * 60)
    print("TEST 5: Integrated Pattern Discovery")
    print("=" * 60)

    # Generate test data
    ts = generate_test_time_series(250)

    try:
        # Initialize integrated discovery
        discovery = IntegratedPatternDiscovery()

        # Discover using all methods
        result = discovery.discover_all_patterns(
            ts,
            methods=['matrix_profile', 'wavelet', 'sax']  # Skip multiscale for speed
        )

        print(f"✓ Integrated discovery completed")
        print(f"  Total patterns found: {result['patterns_found']}")

        # Method stats
        for method, stats in result['method_stats'].items():
            print(f"  {method}: {stats['patterns_found']} patterns")

        # Top patterns
        print(f"✓ Top patterns:")
        for pattern in result['top_patterns'][:5]:
            print(f"  - {pattern['pattern_id']} ({pattern['type']}): "
                  f"validation={pattern['validation_score']:.3f}")

        # Library statistics
        lib_stats = result['statistics']
        print(f"✓ Library statistics:")
        print(f"  Unique signatures: {lib_stats['unique_signatures']}")
        print(f"  Multi-method patterns: {lib_stats['multi_method_patterns']}")

        return True

    except Exception as e:
        print(f"✗ Integrated discovery test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_temporal_network():
    """Test Temporal Network Analysis."""
    print("\n" + "=" * 60)
    print("TEST 6: Temporal Network Analysis")
    print("=" * 60)

    try:
        # Test bursty event detection
        from datetime import datetime, timedelta

        # Generate test events
        base_time = datetime.now()
        events = []

        # Normal period
        for i in range(20):
            ts = base_time + timedelta(days=i)
            events.append((ts, f"pol_{i % 5}", f"pol_{(i + 1) % 5}"))

        # Burst period (many events on one day)
        burst_day = base_time + timedelta(days=25)
        for i in range(15):
            events.append((burst_day, f"pol_{i % 5}", f"pol_{(i + 2) % 5}"))

        # Normal period again
        for i in range(20):
            ts = base_time + timedelta(days=30 + i)
            events.append((ts, f"pol_{i % 5}", f"pol_{(i + 1) % 5}"))

        # Detect bursts
        detector = BurstyEventDetector()
        bursts = detector.detect_bursts(events, min_burst_size=5)

        print(f"✓ Burst detection completed")
        print(f"  Bursts detected: {len(bursts)}")
        for burst in bursts:
            print(f"  - {burst['date']}: {burst['event_count']} events (z={burst['z_score']:.2f})")

        # Test entropy analysis
        # Create mock snapshots
        mock_snapshots = []
        for i in range(5):
            snapshot = {
                'timestamp': (base_time + timedelta(days=i * 30)).isoformat(),
                'network': {
                    'nodes': [{'id': f'pol_{j}'} for j in range(5)],
                    'edges': [
                        {'source': f'pol_{j}', 'target': f'pol_{(j+1)%5}', 'weight': 1}
                        for j in range(5 + i)  # Growing network
                    ]
                }
            }
            mock_snapshots.append(snapshot)

        entropy_analyzer = NetworkEntropyAnalyzer()
        entropy_evolution = entropy_analyzer.compute_temporal_entropy(mock_snapshots)

        print(f"✓ Entropy analysis completed")
        print(f"  Snapshots analyzed: {len(entropy_evolution)}")
        print(f"  Entropy range: {min(e['entropy'] for e in entropy_evolution):.3f} - "
              f"{max(e['entropy'] for e in entropy_evolution):.3f}")

        return True

    except Exception as e:
        print(f"✗ Temporal network test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all Phase 1 integration tests."""
    print("\n" + "=" * 60)
    print("PHASE 1 PATTERN DISCOVERY - INTEGRATION TESTS")
    print("=" * 60)

    tests = [
        ("Matrix Profile", test_matrix_profile),
        ("Multi-Resolution Wavelet", test_multiscale_wavelet),
        ("SAX Patterns", test_sax_patterns),
        ("Multi-Scale Mining", test_multiscale_mining),
        ("Integrated Discovery", test_integrated_discovery),
        ("Temporal Networks", test_temporal_network)
    ]

    results = []

    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"✗ {name} crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
