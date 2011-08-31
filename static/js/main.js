
var Interface = function(container, waterfall) {
    this.container = container;
    this.waterfall = waterfall;

    $(this.container).click(this.dispatch_event)[0].interface = this;
}

$.extend(Interface.prototype, {
    previous_process: null,

    dispatch_event: function(evt) {
        // Only dispatch events for processes.
        if( evt.target.id && evt.target.id[0] == 'p' )
            evt.currentTarget.interface.load_syscalls(evt.target.id.substr(1));
    },

    load_syscalls: function(pid){
        syscalls = this.waterfall.process_syscalls[pid];

        if( this.previous_process )
            $('#p' + this.previous_process).removeClass('selected');

        $('#p' + pid).addClass('selected');
        
        duration = syscalls.slice(-1)[0].duration / 1000;

        html = '<p class=description>Process #' + pid 
               + ' &mdash; Process duration: ' + duration + ' sec.' 
               + '</p>';

        for(s in syscalls) {
            syscall = syscalls[s]
            cmd = syscall.cmd.replace('&', '&amp;')
                             .replace('<', '&lt;')
                             .replace('>', '&gt;');
            html += '<p><span class=cmd>' + cmd + '</span></p>';
        }

        $('#process').html(html);
        $('#process p:first-child').each(function(){this.scrollIntoView();});

        this.previous_process = pid;
    }
});
