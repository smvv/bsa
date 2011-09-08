var Waterfall = function(viewport, dataset_url){
    this.viewport = viewport;
    this.load(dataset_url);
};

$.extend(Waterfall.prototype, {
    dataset_url: null,

    load: function(dataset_url) {
        this.dataset_url = dataset_url;
        html = '<span class="loading">Loading "' + this.dataset_url + '"...</span>';
        $('#waterfall .loading').remove();
        $('#waterfall').append(html);

        $.ajax({
            context: this,
            dataType: 'json',
            url: this.dataset_url,
            error: this.load_error,
            success: this.load_success
        });
    },

    load_error: function(xhr, textStatus, errorThrown) {
        html = '<span class="error">Loading "' + this.dataset_url + '" failed.'
               + '<br/> Error: ' + xhr.status + ' ' + errorThrown + '</span>';
        $('#waterfall .loading').remove();
        $('#waterfall').append(html);
    },

    load_success: function(data, textStatus) {
        $('#waterfall .loading').remove();
        
        this.data = data;
        this.parse_data(data);

        $('#waterfall div:first').click();
    },

    parse_data: function(data) {
        var html = '', pid;

        this.process_syscalls = {};

        pid = data.processes.root.toString();
        html = this.parse_process(data, pid);
        $('#waterfall').html(html);

        html = this.construct_properties(data.properties);
        $('#properties').html(html);
    },

    parse_process: function(data, pid) {
        var html = '';

        if( pid in data.processes ) {
            var process = data.processes[pid];
            this.process_syscalls[pid] = process.syscalls;
        
            if( process.duration < data.properties.threshold * 1000 )
                return html;

            html = this.construct_bar(data, pid);
        }
        else if(console && console.log) {
            console.log('process #' + pid + ' not in data.processes.');
        }
    
        return html;
    },

    construct_bar: function(data, pid) {
        // TODO: currently the parent's left and width are calculated for each
        // child, which is rather inefficient. Try to cache the calculations.
        var process = data.processes[pid],
            left = (process.start - this.viewport.start) * this.viewport.scale,
            width = (process.end - process.start) * this.viewport.scale;

        if( process.parent ) {
            var parent = data.processes[process.parent.toString()];
            left -= (parent.start - this.viewport.start) * this.viewport.scale;
        }

        left = Math.ceil(left);
        width = Math.ceil(width);

        html = '<div id=p' + pid + ' class=' + process.type
               + ' style="margin-left:' + left + 'px;width:' + width + 'px;">';

        for(var c = 0; c < process.children.length; c++) {
            html += this.parse_process(data, process.children[c.toString()]);
        }

        return html + '</div>';
    },

    construct_properties: function(properties) {
        return '<p>Displayed timeline from ' + (this.viewport.start / 1000.0)
               + ' up to ' + (this.viewport.end / 1000.0) + ' seconds. Scale'
               + ' is ' + (1.0/this.viewport.scale) + ' ms/pixel and duration'
               + ' threshold is ' + properties.threshold + ' seconds.</p>';
    }
});
