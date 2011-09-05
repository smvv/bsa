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

        $('#waterfall div:first-child').click();
    },

    parse_data: function(data) {
        var html = '', pid;

        this.process_syscalls = {};

        for( t in data.timeline ) {
            pid = data.timeline[t].toString();
            this.process_syscalls[pid] = data.processes[pid].syscalls;
            html += this.construct_bar(pid, data.processes[pid]);
        }

        $('#waterfall').html(html);

        html = this.construct_properties(data.properties);
        $('#properties').html(html);
    },

    construct_bar: function(pid, process) {
        var left = (process.start - this.viewport.start) * this.viewport.scale,
            width = (process.end - process.start) * this.viewport.scale;

        left = Math.ceil(left);
        width = Math.ceil(width);

        return '<div id=p' + pid + ' class=' + process.type
               + ' style="margin-left:' + left + 'px;width:' + width + 'px;">'
               + '</div>';
    },

    construct_properties: function(properties) {
        return '<p>Displayed timeline from ' + (this.viewport.start / 1000.0)
               + ' up to ' + (this.viewport.end / 1000.0) + ' seconds. Scale'
               + ' is ' + (1.0/this.viewport.scale) + ' ms/pixel and duration'
               + ' threshold is ' + properties.threshold + ' seconds.</p>';
    }
});
