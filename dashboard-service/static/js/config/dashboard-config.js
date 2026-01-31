/**
 * Visualizer Configuration
 * Central configuration for frontend visualization settings
 */

window.DashboardConfig = {
    // UI Configuration
    ui: {
        max_table_rows: 1000,
        animation_duration: 300,  // milliseconds
        tooltip_delay: 500,       // milliseconds
        chart_height: 200,        // pixels
        chart_width: 600,         // pixels
        theme: "light",
        show_legends: true,
        definition_hovers: {
            risks: true,
            controls: true,
            questions: true,
            definitions: false
        }
    },
    
    // Visualization Configuration
    visualization: {
        max_items: 50,
        animation_duration: 750,  // milliseconds
        network: {
            node_radius: 8,
            link_distance: 100,
            charge_strength: -300,
            zoom_scale_extent: [0.1, 10]
        },
        sankey: {
            node_width: 20,
            node_padding: 20
        }
    },
    
    // Search Configuration
    search: {
        max_results: 50,
        timeout: 5000,           // milliseconds
        debounce_delay: 300,     // milliseconds
        min_query_length: 2
    },
    
    // API Configuration
    api: {
        limits: {
            default_limit: 100,
            max_limit: 1000,
            search_limit: 50,
            relationships_limit: 1000
        },
        timeouts: {
            request_timeout: 30000,  // milliseconds
            search_timeout: 5000,    // milliseconds
            debounce_delay: 300      // milliseconds
        }
    },
    
    // Color Configuration
    colors: {
        risk: "#ffbf00",
        control: "#00b0f0",
        question: "#6f30a0",
        success: "#a8d973",
        error: "#dc2626",
        warning: "#fbbc04",
        text: "#333333",
        text_secondary: "#666666"
    },
    
    // External Dependencies
    dependencies: {
        d3_js: "https://d3js.org/d3.v7.min.js",
        d3_sankey: "https://unpkg.com/d3-sankey@0.12.3/dist/d3-sankey.min.js"
    }
};

// Helper functions for configuration access
window.getConfig = function(path, defaultValue = null) {
    const keys = path.split('.');
    let current = window.DashboardConfig;
    
    for (const key of keys) {
        if (current && typeof current === 'object' && key in current) {
            current = current[key];
        } else {
            return defaultValue;
        }
    }
    
    return current;
};

// Override configuration from server-side config if available
if (typeof window.serverConfig !== 'undefined') {
    // Merge server config with default config
    Object.assign(window.DashboardConfig, window.serverConfig);
}