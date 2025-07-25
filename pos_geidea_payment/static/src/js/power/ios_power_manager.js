/** @odoo-module */

import { _t } from "@web/core/l10n/translation";

/**
 * iOS Power Manager
 * Handles power management and battery optimization for iOS devices
 */
export class IOSPowerManager extends EventTarget {
    constructor(options = {}) {
        super();
        
        this.options = {
            lowBatteryThreshold: options.lowBatteryThreshold || 20,
            criticalBatteryThreshold: options.criticalBatteryThreshold || 10,
            powerSaveMode: options.powerSaveMode !== false,
            monitoringInterval: options.monitoringInterval || 30000, // 30 seconds
            ...options
        };

        this.batteryInfo = {
            level: 100,
            charging: false,
            chargingTime: Infinity,
            dischargingTime: Infinity,
            supported: false
        };

        this.powerState = {
            mode: 'normal', // 'normal', 'low_power', 'critical'
            optimizationsActive: false,
            backgroundMode: false,
            thermalState: 'normal' // 'normal', 'fair', 'serious', 'critical'
        };

        this.monitoringTimer = null;
        this.battery = null;
        
        this._initializePowerManagement();
    }

    // Initialize power management
    async _initializePowerManagement() {
        try {
            // Initialize battery monitoring
            await this._initializeBatteryMonitoring();
            
            // Set up thermal monitoring (iOS specific)
            this._initializeThermalMonitoring();
            
            // Set up visibility change monitoring
            this._initializeVisibilityMonitoring();
            
            // Set up network monitoring
            this._initializeNetworkMonitoring();
            
            // Start monitoring loop
            this._startMonitoring();
            
            this.dispatchEvent(new CustomEvent('powerManagerReady', {
                detail: { batteryInfo: this.batteryInfo, powerState: this.powerState }
            }));
            
        } catch (error) {
            console.warn('Power management initialization failed:', error);
        }
    }

    // Battery monitoring
    async _initializeBatteryMonitoring() {
        if ('getBattery' in navigator) {
            try {
                this.battery = await navigator.getBattery();
                this.batteryInfo.supported = true;
                
                // Update initial battery info
                this._updateBatteryInfo();
                
                // Set up battery event listeners
                this.battery.addEventListener('chargingchange', () => this._updateBatteryInfo());
                this.battery.addEventListener('levelchange', () => this._updateBatteryInfo());
                this.battery.addEventListener('chargingtimechange', () => this._updateBatteryInfo());
                this.battery.addEventListener('dischargingtimechange', () => this._updateBatteryInfo());
                
            } catch (error) {
                console.warn('Battery API not available:', error);
            }
        }
    }

    _updateBatteryInfo() {
        if (!this.battery) return;

        const oldLevel = this.batteryInfo.level;
        
        this.batteryInfo = {
            level: Math.round(this.battery.level * 100),
            charging: this.battery.charging,
            chargingTime: this.battery.chargingTime,
            dischargingTime: this.battery.dischargingTime,
            supported: true
        };

        // Check for power state changes
        this._checkPowerStateChange(oldLevel);
        
        // Dispatch battery update event
        this.dispatchEvent(new CustomEvent('batteryUpdate', {
            detail: { batteryInfo: this.batteryInfo }
        }));
    }

    _checkPowerStateChange(oldLevel) {
        const newLevel = this.batteryInfo.level;
        const charging = this.batteryInfo.charging;
        
        let newMode = 'normal';
        
        if (!charging) {
            if (newLevel <= this.options.criticalBatteryThreshold) {
                newMode = 'critical';
            } else if (newLevel <= this.options.lowBatteryThreshold) {
                newMode = 'low_power';
            }
        }
        
        if (newMode !== this.powerState.mode) {
            const oldMode = this.powerState.mode;
            this.powerState.mode = newMode;
            
            this._handlePowerModeChange(oldMode, newMode);
        }
    }

    _handlePowerModeChange(oldMode, newMode) {
        this.dispatchEvent(new CustomEvent('powerModeChange', {
            detail: { oldMode, newMode, batteryLevel: this.batteryInfo.level }
        }));

        if (this.options.powerSaveMode) {
            switch (newMode) {
                case 'low_power':
                    this._enableLowPowerMode();
                    break;
                case 'critical':
                    this._enableCriticalPowerMode();
                    break;
                case 'normal':
                    this._disablePowerSaveMode();
                    break;
            }
        }
    }

    // Thermal monitoring (iOS specific)
    _initializeThermalMonitoring() {
        // Monitor for thermal state changes (iOS Safari)
        if ('ondevicemotion' in window) {
            // Use device motion events to infer thermal state
            let motionEventCount = 0;
            let thermalCheckInterval;

            const deviceMotionHandler = () => {
                motionEventCount++;
            };

            window.addEventListener('devicemotion', deviceMotionHandler);

            // Check thermal state every minute
            thermalCheckInterval = setInterval(() => {
                const eventsPerSecond = motionEventCount / 60;
                motionEventCount = 0;

                // Infer thermal state based on event frequency
                // (This is a simplified heuristic)
                if (eventsPerSecond < 10) {
                    this._updateThermalState('serious');
                } else if (eventsPerSecond < 30) {
                    this._updateThermalState('fair');
                } else {
                    this._updateThermalState('normal');
                }
            }, 60000);
        }
    }

    _updateThermalState(newState) {
        const oldState = this.powerState.thermalState;
        
        if (oldState !== newState) {
            this.powerState.thermalState = newState;
            
            this.dispatchEvent(new CustomEvent('thermalStateChange', {
                detail: { oldState, newState }
            }));

            // Apply thermal optimizations
            if (newState === 'serious' || newState === 'critical') {
                this._enableThermalOptimizations();
            } else {
                this._disableThermalOptimizations();
            }
        }
    }

    // Visibility monitoring for background/foreground states
    _initializeVisibilityMonitoring() {
        document.addEventListener('visibilitychange', () => {
            const isBackground = document.hidden;
            this._handleVisibilityChange(isBackground);
        });

        // Page lifecycle API for iOS Safari
        window.addEventListener('pagehide', () => {
            this._handlePageHide();
        });

        window.addEventListener('pageshow', () => {
            this._handlePageShow();
        });
    }

    _handleVisibilityChange(isBackground) {
        const wasBackground = this.powerState.backgroundMode;
        this.powerState.backgroundMode = isBackground;

        if (wasBackground !== isBackground) {
            this.dispatchEvent(new CustomEvent('visibilityChange', {
                detail: { isBackground, timestamp: Date.now() }
            }));

            if (isBackground) {
                this._enterBackgroundMode();
            } else {
                this._exitBackgroundMode();
            }
        }
    }

    _handlePageHide() {
        this._enterBackgroundMode();
        this.dispatchEvent(new CustomEvent('pageHide', {
            detail: { timestamp: Date.now() }
        }));
    }

    _handlePageShow() {
        this._exitBackgroundMode();
        this.dispatchEvent(new CustomEvent('pageShow', {
            detail: { timestamp: Date.now() }
        }));
    }

    // Network monitoring for connection changes
    _initializeNetworkMonitoring() {
        if ('connection' in navigator) {
            const connection = navigator.connection;
            
            const updateNetworkInfo = () => {
                this.dispatchEvent(new CustomEvent('networkChange', {
                    detail: {
                        effectiveType: connection.effectiveType,
                        downlink: connection.downlink,
                        rtt: connection.rtt,
                        saveData: connection.saveData
                    }
                }));

                // Enable data saver mode if needed
                if (connection.saveData || connection.effectiveType === 'slow-2g') {
                    this._enableDataSaverMode();
                } else {
                    this._disableDataSaverMode();
                }
            };

            connection.addEventListener('change', updateNetworkInfo);
            updateNetworkInfo(); // Initial check
        }
    }

    // Power optimization modes
    _enableLowPowerMode() {
        if (this.powerState.optimizationsActive) return;

        this.powerState.optimizationsActive = true;

        // Reduce monitoring frequency
        this._adjustMonitoringFrequency(0.5);

        // Reduce animation frame rate
        this._reduceAnimationFrameRate();

        // Disable non-essential features
        this._disableNonEssentialFeatures();

        this.dispatchEvent(new CustomEvent('lowPowerModeEnabled', {
            detail: { batteryLevel: this.batteryInfo.level }
        }));
    }

    _enableCriticalPowerMode() {
        // Apply all low power optimizations plus additional ones
        this._enableLowPowerMode();

        // Further reduce monitoring
        this._adjustMonitoringFrequency(0.2);

        // Disable animations
        this._disableAnimations();

        // Reduce connection polling
        this._reduceConnectionActivity();

        this.dispatchEvent(new CustomEvent('criticalPowerModeEnabled', {
            detail: { batteryLevel: this.batteryInfo.level }
        }));
    }

    _disablePowerSaveMode() {
        if (!this.powerState.optimizationsActive) return;

        this.powerState.optimizationsActive = false;

        // Restore normal monitoring frequency
        this._adjustMonitoringFrequency(1.0);

        // Restore animations
        this._enableAnimations();

        // Restore normal connection activity
        this._restoreConnectionActivity();

        // Re-enable features
        this._enableNonEssentialFeatures();

        this.dispatchEvent(new CustomEvent('powerSaveModeDisabled'));
    }

    // Thermal optimizations
    _enableThermalOptimizations() {
        // Reduce CPU intensive operations
        this._reduceCPUIntensiveOperations();

        // Throttle animations and transitions
        this._throttleAnimations();

        // Reduce Bluetooth activity
        this._reduceBluetoothActivity();

        this.dispatchEvent(new CustomEvent('thermalOptimizationsEnabled', {
            detail: { thermalState: this.powerState.thermalState }
        }));
    }

    _disableThermalOptimizations() {
        // Restore normal CPU operations
        this._restoreCPUOperations();

        // Restore animations
        this._restoreAnimations();

        // Restore Bluetooth activity
        this._restoreBluetoothActivity();

        this.dispatchEvent(new CustomEvent('thermalOptimizationsDisabled'));
    }

    // Background/foreground mode handling
    _enterBackgroundMode() {
        // Reduce all activities to minimum
        this._pauseNonEssentialTasks();
        this._adjustMonitoringFrequency(0.1); // Very low frequency
        this._suspendAnimations();

        this.dispatchEvent(new CustomEvent('backgroundModeEntered'));
    }

    _exitBackgroundMode() {
        // Resume normal activities
        this._resumeNonEssentialTasks();
        
        // Restore appropriate monitoring frequency based on power state
        const frequency = this.powerState.mode === 'critical' ? 0.2 :
                         this.powerState.mode === 'low_power' ? 0.5 : 1.0;
        this._adjustMonitoringFrequency(frequency);
        
        this._resumeAnimations();

        this.dispatchEvent(new CustomEvent('backgroundModeExited'));
    }

    // Data saver mode
    _enableDataSaverMode() {
        // Reduce data usage
        this._reduceDataUsage();
        
        this.dispatchEvent(new CustomEvent('dataSaverModeEnabled'));
    }

    _disableDataSaverMode() {
        // Restore normal data usage
        this._restoreDataUsage();
        
        this.dispatchEvent(new CustomEvent('dataSaverModeDisabled'));
    }

    // Monitoring
    _startMonitoring() {
        this._stopMonitoring(); // Clear existing timer
        
        this.monitoringTimer = setInterval(() => {
            this._performPeriodicCheck();
        }, this.options.monitoringInterval);
    }

    _stopMonitoring() {
        if (this.monitoringTimer) {
            clearInterval(this.monitoringTimer);
            this.monitoringTimer = null;
        }
    }

    _adjustMonitoringFrequency(factor) {
        const newInterval = this.options.monitoringInterval / factor;
        
        this._stopMonitoring();
        this.monitoringTimer = setInterval(() => {
            this._performPeriodicCheck();
        }, newInterval);
    }

    _performPeriodicCheck() {
        // Check battery status
        if (this.battery) {
            this._updateBatteryInfo();
        }

        // Check memory usage
        this._checkMemoryUsage();

        // Dispatch periodic update
        this.dispatchEvent(new CustomEvent('periodicUpdate', {
            detail: {
                batteryInfo: this.batteryInfo,
                powerState: this.powerState,
                timestamp: Date.now()
            }
        }));
    }

    _checkMemoryUsage() {
        if ('memory' in performance) {
            const memory = performance.memory;
            const usageRatio = memory.usedJSHeapSize / memory.jsHeapSizeLimit;
            
            if (usageRatio > 0.8) {
                this.dispatchEvent(new CustomEvent('highMemoryUsage', {
                    detail: { usageRatio, memory }
                }));
            }
        }
    }

    // Optimization implementations
    _reduceAnimationFrameRate() {
        // Implement animation frame rate reduction
        document.documentElement.style.setProperty('--animation-duration-multiplier', '2');
    }

    _disableNonEssentialFeatures() {
        // Disable non-essential features for power saving
        this.dispatchEvent(new CustomEvent('disableNonEssentialFeatures'));
    }

    _enableNonEssentialFeatures() {
        // Re-enable non-essential features
        this.dispatchEvent(new CustomEvent('enableNonEssentialFeatures'));
    }

    _disableAnimations() {
        document.documentElement.style.setProperty('--animation-play-state', 'paused');
    }

    _enableAnimations() {
        document.documentElement.style.setProperty('--animation-play-state', 'running');
    }

    _throttleAnimations() {
        document.documentElement.style.setProperty('--animation-duration-multiplier', '3');
    }

    _restoreAnimations() {
        document.documentElement.style.setProperty('--animation-duration-multiplier', '1');
    }

    _suspendAnimations() {
        document.documentElement.style.setProperty('--animation-play-state', 'paused');
    }

    _resumeAnimations() {
        document.documentElement.style.setProperty('--animation-play-state', 'running');
    }

    _reduceConnectionActivity() {
        this.dispatchEvent(new CustomEvent('reduceConnectionActivity'));
    }

    _restoreConnectionActivity() {
        this.dispatchEvent(new CustomEvent('restoreConnectionActivity'));
    }

    _reduceBluetoothActivity() {
        this.dispatchEvent(new CustomEvent('reduceBluetoothActivity'));
    }

    _restoreBluetoothActivity() {
        this.dispatchEvent(new CustomEvent('restoreBluetoothActivity'));
    }

    _reduceCPUIntensiveOperations() {
        this.dispatchEvent(new CustomEvent('reduceCPUIntensiveOperations'));
    }

    _restoreCPUOperations() {
        this.dispatchEvent(new CustomEvent('restoreCPUOperations'));
    }

    _pauseNonEssentialTasks() {
        this.dispatchEvent(new CustomEvent('pauseNonEssentialTasks'));
    }

    _resumeNonEssentialTasks() {
        this.dispatchEvent(new CustomEvent('resumeNonEssentialTasks'));
    }

    _reduceDataUsage() {
        this.dispatchEvent(new CustomEvent('reduceDataUsage'));
    }

    _restoreDataUsage() {
        this.dispatchEvent(new CustomEvent('restoreDataUsage'));
    }

    // Public API
    getBatteryInfo() {
        return { ...this.batteryInfo };
    }

    getPowerState() {
        return { ...this.powerState };
    }

    isBatterySupported() {
        return this.batteryInfo.supported;
    }

    isLowPowerMode() {
        return this.powerState.mode === 'low_power';
    }

    isCriticalPowerMode() {
        return this.powerState.mode === 'critical';
    }

    isBackgroundMode() {
        return this.powerState.backgroundMode;
    }

    isOptimizationsActive() {
        return this.powerState.optimizationsActive;
    }

    // Manual control
    enablePowerSaveMode() {
        this._enableLowPowerMode();
    }

    disablePowerSaveMode() {
        this._disablePowerSaveMode();
    }

    updateOptions(newOptions) {
        Object.assign(this.options, newOptions);
    }

    // Cleanup
    destroy() {
        this._stopMonitoring();
        
        // Remove event listeners
        if (this.battery) {
            this.battery.removeEventListener('chargingchange', this._updateBatteryInfo);
            this.battery.removeEventListener('levelchange', this._updateBatteryInfo);
            this.battery.removeEventListener('chargingtimechange', this._updateBatteryInfo);
            this.battery.removeEventListener('dischargingtimechange', this._updateBatteryInfo);
        }
        
        document.removeEventListener('visibilitychange', this._handleVisibilityChange);
        window.removeEventListener('pagehide', this._handlePageHide);
        window.removeEventListener('pageshow', this._handlePageShow);
    }
}