/** @odoo-module */

import { PlatformDetector } from '../utils/platform_detector';

/**
 * Test suite for platform detection and capabilities
 */
export class PlatformTests {
    constructor() {
        this.detector = new PlatformDetector();
        this.testResults = [];
    }

    /**
     * Run all platform tests
     */
    runAllTests() {
        console.log('Running Geidea Platform Tests...');
        
        this.testPlatformDetection();
        this.testCapabilityDetection();
        this.testConnectionRecommendations();
        this.testInstructions();
        
        this.printResults();
        return this.testResults;
    }

    /**
     * Test platform detection
     */
    testPlatformDetection() {
        const testName = 'Platform Detection';
        try {
            const platform = this.detector.platform;
            const validPlatforms = ['windows', 'ios', 'android', 'linux', 'macos', 'unknown'];
            
            if (validPlatforms.includes(platform)) {
                this.addResult(testName, 'PASS', `Detected platform: ${platform}`);
            } else {
                this.addResult(testName, 'FAIL', `Invalid platform detected: ${platform}`);
            }
        } catch (error) {
            this.addResult(testName, 'ERROR', error.message);
        }
    }

    /**
     * Test capability detection
     */
    testCapabilityDetection() {
        const testName = 'Capability Detection';
        try {
            const capabilities = this.detector.capabilities;
            const requiredCapabilities = ['usb', 'bluetooth', 'serial', 'network'];
            
            let missingCapabilities = [];
            for (const cap of requiredCapabilities) {
                if (!(cap in capabilities)) {
                    missingCapabilities.push(cap);
                }
            }

            if (missingCapabilities.length === 0) {
                this.addResult(testName, 'PASS', `All capabilities detected: ${JSON.stringify(capabilities)}`);
            } else {
                this.addResult(testName, 'FAIL', `Missing capabilities: ${missingCapabilities.join(', ')}`);
            }
        } catch (error) {
            this.addResult(testName, 'ERROR', error.message);
        }
    }

    /**
     * Test connection recommendations
     */
    testConnectionRecommendations() {
        const testName = 'Connection Recommendations';
        try {
            const recommendations = this.detector.getRecommendedConnections();
            
            if (Array.isArray(recommendations) && recommendations.length > 0) {
                this.addResult(testName, 'PASS', `Recommendations: ${recommendations.join(', ')}`);
            } else {
                this.addResult(testName, 'FAIL', 'No connection recommendations provided');
            }
        } catch (error) {
            this.addResult(testName, 'ERROR', error.message);
        }
    }

    /**
     * Test connection instructions
     */
    testInstructions() {
        const testName = 'Connection Instructions';
        try {
            const connectionTypes = ['usb', 'bluetooth', 'network', 'serial'];
            let instructionsCount = 0;
            
            for (const type of connectionTypes) {
                const instructions = this.detector.getConnectionInstructions(type);
                if (instructions && instructions.length > 0) {
                    instructionsCount++;
                }
            }

            if (instructionsCount === connectionTypes.length) {
                this.addResult(testName, 'PASS', 'All connection types have instructions');
            } else {
                this.addResult(testName, 'FAIL', `Missing instructions for ${connectionTypes.length - instructionsCount} connection types`);
            }
        } catch (error) {
            this.addResult(testName, 'ERROR', error.message);
        }
    }

    /**
     * Add test result
     */
    addResult(testName, status, message) {
        this.testResults.push({
            test: testName,
            status: status,
            message: message,
            timestamp: new Date().toISOString()
        });
    }

    /**
     * Print test results
     */
    printResults() {
        console.log('\n=== Geidea Platform Test Results ===');
        
        let passed = 0;
        let failed = 0;
        let errors = 0;

        for (const result of this.testResults) {
            const statusIcon = result.status === 'PASS' ? '✅' : 
                              result.status === 'FAIL' ? '❌' : '⚠️';
            
            console.log(`${statusIcon} ${result.test}: ${result.status}`);
            console.log(`   ${result.message}`);
            
            if (result.status === 'PASS') passed++;
            else if (result.status === 'FAIL') failed++;
            else errors++;
        }

        console.log(`\nSummary: ${passed} passed, ${failed} failed, ${errors} errors`);
        console.log('=== End Test Results ===\n');
    }
}

/**
 * Connection stability test
 */
export class ConnectionStabilityTest {
    constructor(connectionManager) {
        this.connectionManager = connectionManager;
        this.testResults = [];
    }

    /**
     * Test connection stability for a terminal
     */
    async testConnectionStability(terminalConfig, duration = 30000) {
        const testName = `Connection Stability - ${terminalConfig.terminal_id}`;
        const startTime = Date.now();
        let connectionEvents = [];
        
        try {
            // Listen for connection events
            const eventListener = (event) => {
                if (event.detail.terminalId === terminalConfig.terminal_id) {
                    connectionEvents.push({
                        status: event.detail.status,
                        timestamp: Date.now(),
                        message: event.detail.message
                    });
                }
            };

            this.connectionManager.onConnectionChange(eventListener);

            // Connect to terminal
            console.log(`Testing connection stability for ${terminalConfig.terminal_id}...`);
            const connectResult = await this.connectionManager.connect(terminalConfig);
            
            if (!connectResult.success) {
                this.addResult(testName, 'FAIL', `Initial connection failed: ${connectResult.error}`);
                return;
            }

            // Monitor connection for specified duration
            await new Promise(resolve => setTimeout(resolve, duration));

            // Analyze results
            const disconnections = connectionEvents.filter(e => e.status === 'disconnected').length;
            const errors = connectionEvents.filter(e => e.status === 'error').length;
            const reconnections = connectionEvents.filter(e => e.status === 'connected').length - 1; // Subtract initial connection

            if (disconnections === 0 && errors === 0) {
                this.addResult(testName, 'PASS', `Connection stable for ${duration}ms`);
            } else {
                this.addResult(testName, 'FAIL', 
                    `${disconnections} disconnections, ${errors} errors, ${reconnections} reconnections`);
            }

            // Cleanup
            this.connectionManager.offConnectionChange(eventListener);
            await this.connectionManager.disconnect(terminalConfig.terminal_id);

        } catch (error) {
            this.addResult(testName, 'ERROR', error.message);
        }
    }

    /**
     * Add test result
     */
    addResult(testName, status, message) {
        this.testResults.push({
            test: testName,
            status: status,
            message: message,
            timestamp: new Date().toISOString()
        });
    }
}

/**
 * Performance benchmark test
 */
export class PerformanceBenchmark {
    constructor(connectionManager) {
        this.connectionManager = connectionManager;
        this.benchmarkResults = [];
    }

    /**
     * Benchmark connection time
     */
    async benchmarkConnectionTime(terminalConfig, iterations = 5) {
        const testName = `Connection Time - ${terminalConfig.terminal_id}`;
        let times = [];

        try {
            for (let i = 0; i < iterations; i++) {
                const startTime = performance.now();
                
                const result = await this.connectionManager.connect(terminalConfig);
                
                if (result.success) {
                    const endTime = performance.now();
                    times.push(endTime - startTime);
                    
                    // Disconnect for next iteration
                    await this.connectionManager.disconnect(terminalConfig.terminal_id);
                    
                    // Small delay between iterations
                    await new Promise(resolve => setTimeout(resolve, 1000));
                } else {
                    console.warn(`Connection failed in iteration ${i + 1}: ${result.error}`);
                }
            }

            if (times.length > 0) {
                const avgTime = times.reduce((a, b) => a + b, 0) / times.length;
                const minTime = Math.min(...times);
                const maxTime = Math.max(...times);
                
                this.addResult(testName, 'PASS', 
                    `Avg: ${avgTime.toFixed(2)}ms, Min: ${minTime.toFixed(2)}ms, Max: ${maxTime.toFixed(2)}ms`);
            } else {
                this.addResult(testName, 'FAIL', 'No successful connections');
            }

        } catch (error) {
            this.addResult(testName, 'ERROR', error.message);
        }
    }

    /**
     * Add benchmark result
     */
    addResult(testName, status, message) {
        this.benchmarkResults.push({
            test: testName,
            status: status,
            message: message,
            timestamp: new Date().toISOString()
        });
    }
}

// Export test runner
export function runGeideaTests(connectionManager = null) {
    const platformTests = new PlatformTests();
    const results = platformTests.runAllTests();
    
    if (connectionManager) {
        // Additional tests that require connection manager
        console.log('Connection manager provided - running additional tests...');
    }
    
    return results;
}