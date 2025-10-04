const App = {
    state: {
        currentPage: 'dashboard',
        alerts: [],
        activeSessions: [],
        allEvents: [], // <-- ADDED: To hold every single log
        thresholds: { medium: 60, high: 80, critical: 95 },
        dataFetchInterval: null,
        settings: null, // Added for settings management
        refreshPaused: false, // NEW: Track if refresh is paused
        lastUserInteraction: Date.now(), // NEW: Track user activity
    },
    
    // --- ENHANCED DATA FETCHING WITH SMART PAUSING ---
    fetchDashboardData: async function() {
        // Don't refresh if we're on settings page or user recently interacted
        if (this.state.currentPage === 'settings') {
            console.log('Skipping refresh - on settings page');
            return;
        }

        // Don't refresh if user interacted in the last 10 seconds
        if (Date.now() - this.state.lastUserInteraction < 5000) {
            console.log('Skipping refresh - recent user interaction');
            return;
        }

        // Don't refresh if manually paused
        if (this.state.refreshPaused) {
            console.log('Refresh paused by user');
            return;
        }

        try {
            // Fetch alerts (high-risk only)
            const alertsResponse = await fetch('http://127.0.0.1:5000/get_alerts');
            if (!alertsResponse.ok) throw new Error('Failed to fetch alerts.');
            const alertsFromServer = await alertsResponse.json();
            this.state.alerts = alertsFromServer.map(a => ({
                ...a,
                time: new Date(a.time),
                anomalyReason: [`Risk Score: ${a.riskScore}`]
            }));

            // Fetch active sessions
            const sessionsResponse = await fetch('http://127.0.0.1:5000/api/active_sessions');
            if (!sessionsResponse.ok) throw new Error('Failed to fetch sessions.');
            this.state.activeSessions = await sessionsResponse.json();

            // --- NEW: Fetch all events ---
            const eventsResponse = await fetch('http://127.0.0.1:5000/api/all_events');
            if (!eventsResponse.ok) throw new Error('Failed to fetch all events.');
            const eventsFromServer = await eventsResponse.json();
            this.state.allEvents = eventsFromServer.map(e => ({
                ...e,
                time: new Date(e.time)
            }));
            
            // Only re-render if not on settings page
            if (this.state.currentPage !== 'settings') {
                this.render();
            }

        } catch (e) {
            console.error("Failed to fetch dashboard data:", e);
        }
    },
    
    // --- UI RENDERING ---
    render: function() {
        const container = document.getElementById('app-container');
        if (!container) return;
        container.innerHTML = `
            ${this.Sidebar()}
            <div class="flex-1 flex flex-col overflow-hidden">
                ${this.Header()}
                <main class="flex-1 overflow-x-hidden overflow-y-auto bg-gray-900 p-6">
                    ${this.PageContent()}
                </main>
            </div>
        `;
        this.addEventListeners();
    },

    PageContent: function() {
        switch (this.state.currentPage) {
            case 'dashboard': return this.DashboardPage();
            case 'sessions': return this.SessionsPage();
            case 'alerts': return this.AlertsPage();
            case 'settings': return this.SettingsPage();
            default: return `<div>Page not found</div>`;
        }
    },
    
    Sidebar: function() {
        const navItems = [
            { id: 'dashboard', icon: 'fa-tachometer-alt', label: 'Dashboard' },
            { id: 'sessions', icon: 'fa-users', label: 'Sessions' },
            { id: 'alerts', icon: 'fa-bell', label: 'Alerts' },
            { id: 'settings', icon: 'fa-cog', label: 'Settings' },
        ];
        return `
            <div class="hidden md:flex flex-col w-16 bg-gray-800">
                <div class="flex items-center justify-center h-16 bg-gray-900">
                    <a href="/" class="text-cyan-400"><i class="fas fa-shield-halved text-2xl"></i></a>
                </div>
                <div class="flex flex-col flex-1 overflow-y-auto">
                    <nav class="flex-1 px-2 py-4 space-y-2">
                        ${navItems.map(item => `
                            <a href="#" data-page="${item.id}" class="sidebar-icon flex items-center justify-center p-3 rounded-lg text-gray-400 ${this.state.currentPage === item.id ? 'active' : ''}" title="${item.label}">
                                <i class="fas ${item.icon} text-xl"></i>
                            </a>
                        `).join('')}
                    </nav>
                </div>
            </div>
        `;
    },

    // --- ENHANCED HEADER WITH REFRESH CONTROLS ---
    Header: function() {
        const titles = {
            dashboard: 'Live Dashboard Overview',
            sessions: 'Privileged Session Management',
            alerts: 'Live Security Alerts',
            settings: 'System Configuration'
        };

        const refreshControls = this.state.currentPage === 'settings' ? 
            `<div class="flex items-center space-x-2 text-sm">
                <span class="text-yellow-400 flex items-center">
                    <i class="fas fa-pause text-xs mr-2"></i>
                    Auto-refresh paused
                </span>
                <button onclick="App.manualRefresh()" class="bg-gray-600 hover:bg-gray-500 text-white px-3 py-1 rounded text-xs">
                    <i class="fas fa-sync mr-1"></i>Manual Refresh
                </button>
            </div>` :
            `<div class="flex items-center space-x-4 text-sm">
                <span class="text-green-400 flex items-center">
                    <i class="fas fa-circle text-xs mr-2 ${this.state.refreshPaused ? '' : 'animate-pulse'}"></i>
                    ${this.state.refreshPaused ? 'Paused' : 'Live'}
                </span>
                <button onclick="App.toggleRefresh()" class="bg-gray-600 hover:bg-gray-500 text-white px-3 py-1 rounded text-xs">
                    <i class="fas fa-${this.state.refreshPaused ? 'play' : 'pause'} mr-1"></i>
                    ${this.state.refreshPaused ? 'Resume' : 'Pause'}
                </button>
            </div>`;

        return `
            <header class="flex justify-between items-center p-4 bg-gray-800 border-b border-gray-700">
                <h1 class="text-xl font-bold text-white">${titles[this.state.currentPage]}</h1>
                <div class="flex items-center space-x-6">
                    ${refreshControls}
                    <a href="/logout" class="text-gray-400 hover:text-white" title="Logout">
                        <i class="fas fa-sign-out-alt text-xl"></i>
                    </a>
                </div>
            </header>
        `;
    },
    
    DashboardPage: function() {
        const criticalAlerts = this.state.alerts.filter(a => a.riskScore >= this.state.thresholds.critical).length;
        const totalAnomalies = this.state.alerts.length;
        const activeSessionCount = this.state.activeSessions.length;
        // Filter for high-risk alerts only (>= 80 risk score)
        const highRiskAlerts = this.state.alerts.filter(a => a.riskScore >= this.state.thresholds.high);
        return `
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div class="bg-gray-800 p-6 rounded-lg flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-400">Active Sessions</p>
                        <p class="text-3xl font-bold text-white">${activeSessionCount}</p>
                    </div>
                    <i class="fas fa-users text-4xl text-cyan-500"></i>
                </div>
                <div class="bg-gray-800 p-6 rounded-lg flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-400">Critical Alerts</p>
                        <p class="text-3xl font-bold text-red-500 ${criticalAlerts > 0 ? 'animate-pulse-fast' : ''}">${criticalAlerts}</p>
                    </div>
                    <i class="fas fa-exclamation-triangle text-4xl text-red-500"></i>
                </div>
                <div class="bg-gray-800 p-6 rounded-lg flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-400">Total Anomalies (Score >= 40)</p>
                        <p class="text-3xl font-bold text-white">${totalAnomalies}</p>
                    </div>
                    <i class="fas fa-bell text-4xl text-yellow-500"></i>
                </div>
                <div class="bg-gray-800 p-6 rounded-lg flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-400">System Health</p>
                        <p class="text-3xl font-bold text-green-500">Normal</p>
                    </div>
                    <i class="fas fa-heartbeat text-4xl text-green-500"></i>
                </div>
            </div>
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
                <div class="bg-gray-800 p-4 rounded-lg">
                    <h3 class="font-bold text-lg mb-4 text-cyan-300">Recent High-Risk Alerts</h3>
                    <div class="max-h-[600px] overflow-y-auto pr-2" style="scrollbar-width: thin; scrollbar-color: #374151 #1f2937;">
                        ${highRiskAlerts.length > 0 ? this.AlertsList(highRiskAlerts.slice(0, 10)) : '<p class="text-gray-500 text-center py-4">No high-risk alerts found.</p>'}
                    </div>
                </div>
                <div class="bg-gray-800 p-4 rounded-lg">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="font-bold text-lg text-cyan-300">Full Event Log</h3>
                        <span class="text-xs text-gray-400">${this.state.allEvents.length} total events</span>
                    </div>
                    <div class="max-h-[600px] overflow-y-auto pr-2" style="scrollbar-width: thin; scrollbar-color: #374151 #1f2937;">
                        ${this.AlertsList(this.state.allEvents)}
                    </div>
                </div>
            </div>
        `;
    },

    SessionsPage: function() {
        if (this.state.activeSessions.length === 0) {
            return `<div class="p-4 bg-gray-800 rounded-lg text-center">No active sessions.</div>`;
        }
        return `
            <div class="bg-gray-800 rounded-lg shadow">
                <div class="overflow-x-auto">
                    <table class="w-full text-sm text-left text-gray-400">
                        <thead class="text-xs uppercase bg-gray-700 text-gray-400">
                            <tr>
                                <th scope="col" class="px-6 py-3">User Email</th>
                                <th scope="col" class="px-6 py-3">Role</th>
                                <th scope="col" class="px-6 py-3">Login Time</th>
                                <th scope="col" class="px-6 py-3">Critical Strikes</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${this.state.activeSessions.map(s => `
                                <tr class="bg-gray-800 border-b border-gray-700 hover:bg-gray-600">
                                    <td class="px-6 py-4 font-medium text-white">${s.email}</td>
                                    <td class="px-6 py-4">${s.role}</td>
                                    <td class="px-6 py-4">${new Date(s.login_time).toLocaleString()}</td>
                                    <td class="px-6 py-4 font-bold ${s.strike_count > 0 ? 'text-yellow-400' : 'text-gray-400'}">${s.strike_count} / 3</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    },

    AlertsPage: function() { 
        return `
            <div class="bg-gray-800 rounded-lg shadow">
                <div class="overflow-x-auto">
                    <table class="w-full text-sm text-left text-gray-400">
                        <thead class="text-xs uppercase bg-gray-700 text-gray-400">
                            <tr>
                                <th scope="col" class="px-6 py-3">Time</th>
                                <th scope="col" class="px-6 py-3">User Role</th>
                                <th scope="col" class="px-6 py-3">Action</th>
                                <th scope="col" class="px-6 py-3">Risk Score</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${this.state.allEvents.map(alert => `
                                <tr class="bg-gray-800 border-b border-gray-700 hover:bg-gray-600">
                                    <td class="px-6 py-4">${alert.time.toLocaleString()}</td>
                                    <td class="px-6 py-4 font-medium text-white">${alert.user.role}</td>
                                    <td class="px-6 py-4 font-mono text-cyan-300">${alert.action}</td>
                                    <td class="px-6 py-4">${this.RiskBadge(alert.riskScore)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    },

    RiskBadge: function(score) { 
        let colorClass, label;
        if (score >= 95) {
            colorClass = 'bg-red-500/20 text-red-300'; label = 'Critical';
        } else if (score >= this.state.thresholds.high) {
            colorClass = 'bg-orange-500/20 text-orange-300'; label = 'High';
        } else if (score >= this.state.thresholds.medium) {
            colorClass = 'bg-yellow-500/20 text-yellow-300'; label = 'Medium';
        } else {
            colorClass = 'bg-gray-500/20 text-gray-300'; label = 'Low';
        }
        return `<span class="px-2 py-1 rounded-full text-xs font-semibold ${colorClass}">${label} (${score})</span>`;
    },

    // Add this new function to your App object in script.js
    getActionDescription: function(action) {
        const descriptions = {
            'DB_CONNECT': 'Established connection to database server',
            'RUN_QUERY': 'Executed SQL query on database',
            'BACKUP_DB': 'Initiated database backup operation',
            'DELETE_TABLE': 'Attempted to delete database table (High Risk)',
            'SSH_ROUTER': 'Established SSH connection to network router',
            'PING_HOST': 'Performed network connectivity test',
            'CHECK_FIREWALL': 'Checked firewall port configuration',
            'SHUTDOWN_ROUTER': 'Attempted router shutdown (Critical Risk)',
            'OAUTH_LOGIN_SUCCESS': 'Successfully authenticated via OAuth',
            'LOGIN_SUCCESS': 'Successfully logged into system',
            'LOGIN_FAILED_WRONG_PASSWORD': 'Failed login attempt - incorrect password',
            'LOGIN_FAILED_NO_USER': 'Failed login attempt - user not found',
            'PORTAL_ACCESS_REVOKED': 'Portal access terminated due to policy violation',
            'START_SERVER': 'Started application server',
            'DEPLOY_APP': 'Deployed application to server',
            'GIT_PULL': 'Retrieved code from version control',
            'CHECK_BILLING': 'Accessed cloud billing information',
            'PROVISION_VM': 'Created new virtual machine instance',
            'SCALE_CLUSTER': 'Modified cluster scaling configuration',
            'UPDATE_IAM': 'Modified identity and access management settings',
            'rm -rf /': 'Attempted destructive file system operation (Critical Risk)'
        };
        
        return descriptions[action] || 'Unknown system action performed';
    },

    // Replace your existing AlertsList function with this enhanced version
    AlertsList: function(events) { 
        if (events.length === 0) return `<p class="text-gray-500 text-center py-4">No events to display.</p>`;
        return `
            <div class="space-y-3">
                ${events.map(event => {
                    // Get action description
                    const actionDescription = this.getActionDescription(event.action);
                    
                    // Format details if they exist
                    let detailsHtml = '';
                    if (event.details && Object.keys(event.details).length > 0) {
                        const detailsString = Object.entries(event.details)
                            .map(([key, value]) => `${key.replace('_', ' ')}: ${value}`)
                            .join(', ');
                        detailsHtml = `<pre class="text-xs text-gray-400 mt-2 p-2 bg-gray-800 rounded-md whitespace-pre-wrap">${detailsString}</pre>`;
                    }
                    return `
                        <div class="p-3 rounded-lg bg-gray-700/50">
                            <div class="flex justify-between items-center">
                                <div class="flex-1">
                                    <p class="text-sm font-semibold text-white">${event.user.role} - ${event.action}</p>
                                    <p class="text-xs text-gray-300 mt-1 italic">${actionDescription}</p>
                                </div>
                                ${this.RiskBadge(event.riskScore)}
                            </div>
                            <p class="text-xs text-gray-500 mt-2">${event.time.toLocaleString()}</p>
                            ${detailsHtml}
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    },

    // --- SETTINGS MANAGEMENT ---
    loadSettings: async function() {
        try {
            const response = await fetch('/api/settings');
            if (response.ok) {
                this.state.settings = await response.json();
                // Update local thresholds
                this.state.thresholds = this.state.settings.risk_thresholds;
            }
        } catch (error) {
            console.error('Failed to load settings:', error);
        }
    },

    saveSettings: async function(settingsData) {
        try {
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settingsData)
            });
            
            const result = await response.json();
            if (response.ok) {
                this.showNotification('Settings saved successfully!', 'success');
                this.loadSettings(); // Reload settings
            } else {
                this.showNotification(result.error, 'error');
            }
        } catch (error) {
            this.showNotification('Failed to save settings', 'error');
        }
    },

    // --- ENHANCED SETTINGS PAGE WITH USER INTERACTION TRACKING ---
    SettingsPage: function() {
        // Initialize settings if not loaded
        if (!this.state.settings) {
            this.loadSettings();
            return `
                <div class="p-4 bg-gray-800 rounded-lg text-center">
                    <i class="fas fa-spinner fa-spin text-2xl text-cyan-400 mb-4"></i>
                    <p>Loading system configuration...</p>
                </div>
            `;
        }

        const settings = this.state.settings;
        
        return `
            <div class="space-y-6" onclick="App.trackUserInteraction()" onkeypress="App.trackUserInteraction()" oninput="App.trackUserInteraction()">
                
                <!-- Refresh Status Notice -->
                <div class="bg-blue-800/30 border border-blue-600/50 p-4 rounded-lg">
                    <div class="flex items-center">
                        <i class="fas fa-info-circle text-blue-400 mr-3"></i>
                        <div>
                            <h4 class="text-blue-300 font-medium">Auto-refresh Paused</h4>
                            <p class="text-sm text-blue-200">Data updates are paused while you configure settings. Use "Manual Refresh" to update data if needed.</p>
                        </div>
                    </div>
                </div>

                <!-- Risk Score Configuration -->
                <div class="bg-gray-800 p-6 rounded-lg">
                    <h3 class="text-lg font-semibold text-white mb-4 flex items-center">
                        <i class="fas fa-exclamation-triangle text-yellow-500 mr-3"></i>
                        Risk Score Thresholds
                    </h3>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-2">Medium Risk (Yellow)</label>
                            <input type="number" value="${settings.risk_thresholds.medium}" min="1" max="100" 
                                   class="w-full bg-gray-700 border border-gray-600 text-white text-sm rounded-lg p-2.5"
                                   id="medium-threshold" onchange="App.trackUserInteraction()">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-2">High Risk (Orange)</label>
                            <input type="number" value="${settings.risk_thresholds.high}" min="1" max="100"
                                   class="w-full bg-gray-700 border border-gray-600 text-white text-sm rounded-lg p-2.5"
                                   id="high-threshold" onchange="App.trackUserInteraction()">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-2">Critical Risk (Red)</label>
                            <input type="number" value="${settings.risk_thresholds.critical}" min="1" max="100"
                                   class="w-full bg-gray-700 border border-gray-600 text-white text-sm rounded-lg p-2.5"
                                   id="critical-threshold" onchange="App.trackUserInteraction()">
                        </div>
                    </div>
                    <button onclick="App.updateThresholds()" class="mt-4 bg-cyan-600 hover:bg-cyan-700 text-white font-medium py-2 px-4 rounded-lg">
                        Update Thresholds
                    </button>
                </div>

                <!-- Session Management -->
                <div class="bg-gray-800 p-6 rounded-lg">
                    <h3 class="text-lg font-semibold text-white mb-4 flex items-center">
                        <i class="fas fa-users text-cyan-500 mr-3"></i>
                        Session Management
                    </h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-2">Max Strike Count (Auto-Revoke)</label>
                            <input type="number" value="${settings.session_management.max_strikes}" min="1" max="10"
                                   class="w-full bg-gray-700 border border-gray-600 text-white text-sm rounded-lg p-2.5"
                                   id="max-strikes" onchange="App.trackUserInteraction()">
                            <p class="text-xs text-gray-400 mt-1">Number of critical actions before portal access is revoked</p>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-2">Session Timeout (minutes)</label>
                            <input type="number" value="${settings.session_management.session_timeout}" min="5" max="480"
                                   class="w-full bg-gray-700 border border-gray-600 text-white text-sm rounded-lg p-2.5"
                                   id="session-timeout" onchange="App.trackUserInteraction()">
                            <p class="text-xs text-gray-400 mt-1">Automatic logout after inactivity</p>
                        </div>
                    </div>
                </div>

                <!-- Dashboard Refresh Settings -->
                <div class="bg-gray-800 p-6 rounded-lg">
                    <h3 class="text-lg font-semibold text-white mb-4 flex items-center">
                        <i class="fas fa-sync text-green-500 mr-3"></i>
                        Dashboard Refresh Settings
                    </h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-2">Refresh Interval (seconds)</label>
                            <select class="w-full bg-gray-700 border border-gray-600 text-white text-sm rounded-lg p-2.5" 
                                    id="refresh-interval" onchange="App.trackUserInteraction(); App.updateRefreshInterval();">
                                <option value="1" ${settings.dashboard.refresh_interval === 1 ? 'selected' : ''}>1 second (High CPU)</option>
                                <option value="3" ${settings.dashboard.refresh_interval === 3 ? 'selected' : ''}>3 seconds</option>
                                <option value="5" ${settings.dashboard.refresh_interval === 5 ? 'selected' : ''}>5 seconds (Recommended)</option>
                                <option value="10" ${settings.dashboard.refresh_interval === 10 ? 'selected' : ''}>10 seconds</option>
                                <option value="30" ${settings.dashboard.refresh_interval === 30 ? 'selected' : ''}>30 seconds</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-2">Max Events Displayed</label>
                            <select class="w-full bg-gray-700 border border-gray-600 text-white text-sm rounded-lg p-2.5" 
                                    id="max-events" onchange="App.trackUserInteraction()">
                                <option value="25" ${settings.dashboard.max_events === 25 ? 'selected' : ''}>25 events</option>
                                <option value="50" ${settings.dashboard.max_events === 50 ? 'selected' : ''}>50 events (Default)</option>
                                <option value="100" ${settings.dashboard.max_events === 100 ? 'selected' : ''}>100 events</option>
                                <option value="200" ${settings.dashboard.max_events === 200 ? 'selected' : ''}>200 events</option>
                                <option value="-1" ${settings.dashboard.max_events === -1 ? 'selected' : ''}>All events (may be slow)</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- Alert & Notification Settings -->
                <div class="bg-gray-800 p-6 rounded-lg">
                    <h3 class="text-lg font-semibold text-white mb-4 flex items-center">
                        <i class="fas fa-bell text-red-500 mr-3"></i>
                        Alert & Notification Settings
                    </h3>
                    <div class="space-y-4">
                        <div class="flex items-center justify-between">
                            <div>
                                <label class="text-sm font-medium text-gray-300">Real-time Email Alerts</label>
                                <p class="text-xs text-gray-400">Send email notifications for critical events</p>
                            </div>
                            <input type="checkbox" ${settings.alerts.email_enabled ? 'checked' : ''} 
                                   id="email-enabled" class="w-4 h-4 text-cyan-600 bg-gray-700 border-gray-600 rounded"
                                   onchange="App.trackUserInteraction()">
                        </div>
                        <div class="flex items-center justify-between">
                            <div>
                                <label class="text-sm font-medium text-gray-300">Slack Integration</label>
                                <p class="text-xs text-gray-400">Post alerts to Slack security channel</p>
                            </div>
                            <input type="checkbox" ${settings.alerts.slack_enabled ? 'checked' : ''}
                                   id="slack-enabled" class="w-4 h-4 text-cyan-600 bg-gray-700 border-gray-600 rounded"
                                   onchange="App.trackUserInteraction()">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-2">Alert Email Recipients</label>
                            <textarea rows="3" id="email-recipients" 
                                      class="w-full bg-gray-700 border border-gray-600 text-white text-sm rounded-lg p-2.5"
                                      onchange="App.trackUserInteraction()">${settings.alerts.email_recipients.join(', ')}</textarea>
                        </div>
                        <button onclick="App.sendTestAlert()" class="bg-yellow-600 hover:bg-yellow-700 text-white font-medium py-2 px-4 rounded-lg">
                            <i class="fas fa-paper-plane mr-2"></i>Send Test Alert
                        </button>
                    </div>
                </div>

                <!-- System Health Check -->
                <div class="bg-gray-800 p-6 rounded-lg">
                    <h3 class="text-lg font-semibold text-white mb-4 flex items-center">
                        <i class="fas fa-heartbeat text-green-500 mr-3"></i>
                        System Status & Health
                    </h3>
                    <div id="health-status-grid" class="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                        <!-- Health status will be populated by checkSystemHealth() -->
                        <div class="bg-gray-700 p-4 rounded-lg">
                            <i class="fas fa-spinner fa-spin text-2xl text-gray-400 mb-2"></i>
                            <p class="text-sm text-gray-300">Click "Run Health Check"</p>
                            <p class="text-lg font-bold text-gray-400">to see status</p>
                        </div>
                    </div>
                    <button onclick="App.checkSystemHealth()" class="mt-4 w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg">
                        <i class="fas fa-sync mr-2"></i>Run System Health Check
                    </button>
                </div>

                <!-- Log Management -->
                <div class="bg-gray-800 p-6 rounded-lg">
                    <h3 class="text-lg font-semibold text-white mb-4 flex items-center">
                        <i class="fas fa-file-alt text-blue-500 mr-3"></i>
                        Log Management
                    </h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-2">Log Retention Period</label>
                            <select class="w-full bg-gray-700 border border-gray-600 text-white text-sm rounded-lg p-2.5" 
                                    id="log-retention" onchange="App.trackUserInteraction()">
                                <option value="7" ${settings.logs.retention_days === 7 ? 'selected' : ''}>7 days</option>
                                <option value="30" ${settings.logs.retention_days === 30 ? 'selected' : ''}>30 days</option>
                                <option value="90" ${settings.logs.retention_days === 90 ? 'selected' : ''}>90 days</option>
                                <option value="365" ${settings.logs.retention_days === 365 ? 'selected' : ''}>1 year</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-2">Log Level</label>
                            <select class="w-full bg-gray-700 border border-gray-600 text-white text-sm rounded-lg p-2.5" 
                                    id="log-level" onchange="App.trackUserInteraction()">
                                <option value="debug" ${settings.logs.log_level === 'debug' ? 'selected' : ''}>Debug (All events)</option>
                                <option value="info" ${settings.logs.log_level === 'info' ? 'selected' : ''}>Info (Standard)</option>
                                <option value="warn" ${settings.logs.log_level === 'warn' ? 'selected' : ''}>Warning (Medium+ risk)</option>
                                <option value="error" ${settings.logs.log_level === 'error' ? 'selected' : ''}>Error (High+ risk only)</option>
                            </select>
                        </div>
                    </div>
                    <div class="space-y-2">
                        <button onclick="App.exportLogs()" class="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg mr-2">
                            <i class="fas fa-download mr-2"></i>Export Logs
                        </button>
                        <button onclick="App.clearOldLogs()" class="bg-yellow-600 hover:bg-yellow-700 text-white font-medium py-2 px-4 rounded-lg mr-2">
                            <i class="fas fa-broom mr-2"></i>Clear Old Logs
                        </button>
                        <button onclick="App.clearAllLogs()" class="bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg">
                            <i class="fas fa-trash mr-2"></i>Clear All Logs
                        </button>
                    </div>
                </div>

                <!-- Save All Changes -->
                <div class="bg-gray-700 p-4 rounded-lg text-center">
                    <button onclick="App.saveAllSettings()" class="bg-cyan-600 hover:bg-cyan-700 text-white font-bold py-3 px-8 rounded-lg text-lg">
                        <i class="fas fa-save mr-2"></i>Save All Configuration Changes
                    </button>
                    <p class="text-xs text-gray-400 mt-2">Changes will be applied immediately and logged for audit</p>
                </div>
            </div>
        `;
    },

    // --- NEW REFRESH CONTROL FUNCTIONS ---
    toggleRefresh: function() {
        this.state.refreshPaused = !this.state.refreshPaused;
        this.render(); // Update the header to show new state
    },

    manualRefresh: function() {
        // Force refresh regardless of pause state
        const wasPaused = this.state.refreshPaused;
        this.state.refreshPaused = false;
        this.fetchDashboardData();
        this.state.refreshPaused = wasPaused; // Restore pause state
        this.showNotification('Data refreshed manually', 'info');
    },

    trackUserInteraction: function() {
        this.state.lastUserInteraction = Date.now();
    },

    updateRefreshInterval: function() {
        const newInterval = parseInt(document.getElementById('refresh-interval').value) * 1000;
        
        // Clear existing interval
        if (this.state.dataFetchInterval) {
            clearInterval(this.state.dataFetchInterval);
        }
        
        // Set new interval
        this.state.dataFetchInterval = setInterval(() => this.fetchDashboardData(), newInterval);
        
        this.showNotification(`Refresh interval updated to ${newInterval/1000} seconds`, 'success');
    },

    // --- SETTINGS FUNCTIONS ---
    updateThresholds: async function() {
        const medium = parseInt(document.getElementById('medium-threshold').value);
        const high = parseInt(document.getElementById('high-threshold').value);
        const critical = parseInt(document.getElementById('critical-threshold').value);
        
        if (medium >= high || high >= critical) {
            this.showNotification('Error: Thresholds must be in ascending order (Medium < High < Critical)', 'error');
            return;
        }
        
        await this.saveSettings({
            risk_thresholds: { medium, high, critical }
        });
    },

    saveAllSettings: async function() {
        try {
            const newSettings = {
                risk_thresholds: {
                    medium: parseInt(document.getElementById('medium-threshold').value),
                    high: parseInt(document.getElementById('high-threshold').value),
                    critical: parseInt(document.getElementById('critical-threshold').value)
                },
                session_management: {
                    max_strikes: parseInt(document.getElementById('max-strikes').value),
                    session_timeout: parseInt(document.getElementById('session-timeout').value)
                },
                alerts: {
                    email_enabled: document.getElementById('email-enabled').checked,
                    slack_enabled: document.getElementById('slack-enabled').checked,
                    email_recipients: document.getElementById('email-recipients').value.split(',').map(email => email.trim())
                },
                dashboard: {
                    refresh_interval: parseInt(document.getElementById('refresh-interval').value),
                    max_events: parseInt(document.getElementById('max-events').value)
                },
                logs: {
                    retention_days: parseInt(document.getElementById('log-retention').value),
                    log_level: document.getElementById('log-level').value
                }
            };
            
            await this.saveSettings(newSettings);
        } catch (error) {
            this.showNotification('Failed to save settings', 'error');
        }
    },

    // --- SYSTEM HEALTH ---
    checkSystemHealth: async function() {
        try {
            const response = await fetch('/api/system-health');
            if (response.ok) {
                const health = await response.json();
                this.displayHealthStatus(health);
            } else {
                this.showNotification('Failed to check system health', 'error');
            }
        } catch (error) {
            this.showNotification('Health check failed', 'error');
        }
    },

    displayHealthStatus: function(health) {
        const statusGrid = document.getElementById('health-status-grid');
        if (!statusGrid) return;
        
        const components = [
            { name: 'Database', key: 'database', icon: 'fa-database' },
            { name: 'Log Watcher', key: 'log_watcher', icon: 'fa-eye' },
            { name: 'ML Model', key: 'ml_model', icon: 'fa-brain' },
            { name: 'Disk Space', key: 'disk_space', icon: 'fa-hdd' },
            { name: 'Memory', key: 'memory_usage', icon: 'fa-memory' },
            { name: 'CPU Usage', key: 'cpu_usage', icon: 'fa-microchip' }
        ];
        
        statusGrid.innerHTML = components.map(comp => {
            const status = health[comp.key] || 'unknown';
            let colorClass = 'text-gray-400';
            if (status === 'online' || status === 'running' || status === 'active' || status === 'normal') {
                colorClass = 'text-green-400';
            } else if (status === 'warning') {
                colorClass = 'text-yellow-400';
            } else if (status === 'critical' || status === 'offline' || status === 'stopped') {
                colorClass = 'text-red-400';
            }
            
            return `
                <div class="bg-gray-700 p-4 rounded-lg">
                    <i class="fas ${comp.icon} text-2xl ${colorClass} mb-2"></i>
                    <p class="text-sm text-gray-300">${comp.name}</p>
                    <p class="text-lg font-bold ${colorClass}">${status}</p>
                </div>
            `;
        }).join('');
    },

    // --- LOG MANAGEMENT ---
    exportLogs: async function() {
        try {
            this.showNotification('Preparing log export...', 'info');
            const response = await fetch('/api/export-logs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ date_range: 30 })
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showNotification('Logs exported successfully!', 'success');
                // Trigger download
                window.open(result.download_url, '_blank');
            } else {
                this.showNotification('Failed to export logs', 'error');
            }
        } catch (error) {
            this.showNotification('Export failed', 'error');
        }
    },

    clearOldLogs: async function() {
        if (!confirm('Clear old log entries? This action cannot be undone.')) return;
        
        try {
            const response = await fetch('/api/clear-logs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'clear_old' })
            });
            
            if (response.ok) {
                this.showNotification('Old logs cleared successfully', 'success');
            } else {
                this.showNotification('Failed to clear logs', 'error');
            }
        } catch (error) {
            this.showNotification('Clear operation failed', 'error');
        }
    },

    clearAllLogs: async function() {
        if (!confirm('⚠️ DANGER: Clear ALL logs? This will permanently delete all event history!')) return;
        if (!confirm('Are you absolutely sure? This cannot be undone!')) return;
        
        try {
            const response = await fetch('/api/clear-logs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'clear_all' })
            });
            
            if (response.ok) {
                this.showNotification('All logs cleared', 'success');
                // Refresh the dashboard data
                this.fetchDashboardData();
            } else {
                this.showNotification('Failed to clear logs', 'error');
            }
        } catch (error) {
            this.showNotification('Clear operation failed', 'error');
        }
    },

    sendTestAlert: async function() {
        try {
            const response = await fetch('/api/send-test-alert', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showNotification('Test alert sent successfully!', 'success');
            } else {
                this.showNotification('Failed to send test alert', 'error');
            }
        } catch (error) {
            this.showNotification('Test alert failed', 'error');
        }
    },

    // --- NOTIFICATION SYSTEM ---
    showNotification: function(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
            type === 'success' ? 'bg-green-600' : 
            type === 'error' ? 'bg-red-600' : 
            type === 'warning' ? 'bg-yellow-600' : 'bg-blue-600'
        } text-white`;
        
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas ${
                    type === 'success' ? 'fa-check-circle' : 
                    type === 'error' ? 'fa-exclamation-circle' : 
                    type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle'
                } mr-2"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    },
    
    // --- ENHANCED EVENT LISTENERS ---
    addEventListeners: function() {
        document.querySelectorAll('.sidebar-icon').forEach(icon => {
            icon.addEventListener('click', (e) => {
                e.preventDefault();
                this.state.currentPage = e.currentTarget.dataset.page;
                this.trackUserInteraction(); // Track navigation as interaction
                this.render();
            });
        });
    },

    // --- ENHANCED INITIALIZATION ---
    init: function() {
        this.loadSettings();
        this.fetchDashboardData();
        // Start with 5-second interval (more reasonable default)
        this.state.dataFetchInterval = setInterval(() => this.fetchDashboardData(), 5000);
    }
};

// Check if we are on the main dashboard page before initializing
if (document.getElementById('app-container')) {
    App.init();
}