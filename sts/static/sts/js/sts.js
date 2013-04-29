(function() {

    var STSconfig = this.STSconfig || {};

    this.STS = STS = {
        Models: {},
        Views: {},
        config: STSconfig
    };

    var transitionTemplate = [
        '<div class="span8 details">',
            '<div class=delay><%= data.delay %></div>',
            '<h4><span class=state><%= data.state %></span>',
                '<small class=event><%= data.event %></small></h4>',
            '<p class=message><%= data.message %></p>',
        '</div>',
        '<div class="span4 stats">',
            '<div class=progress>',
                '<div class=bar></div>',
            '</div>',
            '<div class=duration><%= data.natural_duration %></div>',
        '</div>'
    ].join(' ')


    var systemTemplate = [
        '<h3><span class=name><%= data.name %></span>',
            '<% if (data.content_type) { %><small><%= data.content_type %></small><% } %>',
        '</h3>',
        '<p class=meta><%= data.created %> &middot; <%= data.modified %></p>',
        '<div class=transitions></div>'
    ].join(' ');


    var systemLinkTemplate = [
        '<i class=icon-circle></i>',
        '<a href="<%= data.url %>">',
            '<% if (data.content_type) { %><small><%= data.content_type %>:</small><% } %>',
            '<%= data.name %>',
        '</a>'
    ].join(' ');


    function renderTime(str) {
        var date = Date.parse(str.split('.')[0]),
            hours = date.getHours(),
            minutes = '0' + date.getMinutes(),
            seconds = '0' + date.getSeconds(),
            tod = 'am';

        if (hours > 12) {
            hours = hours - 12;
            tod = 'pm';
        }

        return [
            date.getMonth() + 1,
            date.getDate(),
            date.getFullYear()
        ].join('/') + ' @ ' + [
            hours,
            minutes.substr(minutes.length - 2),
            seconds.substr(seconds.length - 2),
        ].join(':') + ' ' + tod;
    }


    // Read-only collection, this currently does not expect views to
    // be removed
    var CollectionView = Backbone.View.extend({
        childView: Backbone.View,

        initialize: function() {
            this.listenTo(this.collection, 'reset', this.reset, this);
            this.listenTo(this.collection, 'add', this.add, this);
        },

        render: function() {
            return this;
        },

        renderChild: function(view) {
            view.render();
            this.$el.append(view.el);
            return view;
        },

        reset: function(collection, options) {
            var _this = this;
            this.$el.empty();
            collection.each(function(model) {
                _this.add(model, collection, options);
            });
        },

        add: function(model, collection, options) {
            var view = new this.childView({
                model: model
            });
            return this.renderChild(view);
        }
    });


    var SystemModel = Backbone.Model.extend({
        options: {
            poll: false,
            interval: 5000
        },

        url: function() {
            return this.get('url');
        },

        constructor: function(attrs, options) {
            this.transitions = new TransitionCollection;
            Backbone.Model.apply(this, arguments);
            _.extend(this.options, _.pick(options, ['poll', 'interval']));
        },

        initialize: function() {
            if (this.options.poll) this.startPolling();
        },

        parse: function(attrs, options) {
            if (attrs.transitions != null) {
                this.transitions.set(attrs.transitions, options);
                delete attrs.transitions;
            }
            return attrs;
        },

        startPolling: function() {
            this.stopPolling();
            this.fetch({parse: true});

            var _this = this;
            this._pollInterval = setInterval(function() {
                _this.fetch({parse: true});
            }, this.options.interval);
        },

        stopPolling: function() {
            clearInterval(this._pollInterval);
        }
    });


    var SystemCollection = Backbone.Collection.extend({
        model: SystemModel,

        options: {
            poll: true,
            interval: 60 * 1000
        },

        initialize: function() {
            if (this.options.poll) this.startPolling({reset: true});
        },

        startPolling: function(options) {
            this.stopPolling();
            this.fetch(options);

            var _this = this;
            this._pollInterval = setInterval(function() {
                _this.fetch();
            }, this.options.interval);
        },

        stopPolling: function() {
            clearInterval(this._pollInterval);
        }
    });


    var TransitionModel = Backbone.Model.extend({
        maxDuration: function() {
            return this.collection.maxDuration();
        }
    });


    var TransitionCollection = Backbone.Collection.extend({
        model: TransitionModel,

        maxDuration: function() {
            if (!this.length) return;
            return this.max(function(model) {
                return model.get('duration');
            }).get('duration');
        }
    });


    var Transition = Backbone.View.extend({
        className: 'transition row-fluid',

        template: _.template(transitionTemplate, null, {
            variable: 'data'
        }),

        initialize: function() {
            this.$el.html(this.template(this.model.toJSON()));

            this.$delay = this.$('.delay');
            this.$state = this.$('.state');
            this.$event = this.$('.event');
            this.$progress = this.$('.progress');
            this.$message = this.$('.message');
            this.$bar = this.$('.progress .bar');
            this.$duration = this.$('.duration');

            this.listenTo(this.model, 'change', this.render, this);
        },

        durationPercentage: function() {
            return (this.model.get('duration') / this.model.maxDuration() * 100) + '%';
        },

        render: function() {
            var data = this.model.toJSON();

            this.$state.text(data.state);

            if (data.message) {
                this.$message.show().text(data.message);
            } else {
                this.$message.hide();
            }

            if (data.event) {
                this.$event.show().text(data.event);
            } else {
                this.$event.hide();
            }

            if (data.duration == 0) {
                this.$duration.hide();
                this.$progress.hide();
            } else {
                this.$duration.show().text(data.natural_duration);
                this.$progress.show()[0].className = 'progress';

                if (data.failed == true) {
                    this.$progress.addClass('progress-danger');
                } else if (data.end_time == null) {
                    this.$progress.addClass('progress-striped active');
                } else {
                    this.$progress.addClass('progress-success');
                }

                this.$bar.css({
                    width: this.durationPercentage()
                });
            }

            return this;
        },
    });

    var Transitions = CollectionView.extend({
        childView: Transition,

        renderChild: function(view) {
            view.render();
            this.$el.prepend(view.el);
            return view;
        }
    });


    var System = Backbone.View.extend({
        className: 'system',

        template: _.template(systemTemplate, null, {
            variable: 'data'
        }),

        options: {
            condensed: false
        },

        initialize: function(options) {
            this.listenTo(this.model, 'change', this.render, this);
            this.listenTo(this.model, 'change:visible', this.toggle, this);

            this.$el.html(this.template(this.model.toJSON()));

            this.$name = this.$('.name');
            this.$meta = this.$('.meta');
            this.$transitions = this.$('.transitions');

            this.transitions = new Transitions(_.defaults({
                el: this.$transitions,
                collection: this.model.transitions
            }, options));

            this.$el.append(this.transitions.el);

            if (this.options.condensed) {
                this.$el.addClass('condensed');
            }
        },

        render: function() {
            this.$name.text(this.model.get('name'));

            var created = renderTime(this.model.get('created')),
                modified = renderTime(this.model.get('modified'));

            this.$meta.html('created: ' + created + ' &middot; ' + 'modified: ' + modified);
        },

        toggle: function(model, value, options) {
            this.$el.toggle(this.model.get('visible'));
        }
    });


    var Systems = Backbone.View.extend({
        childView: System,

        initialize: function() {
            this.listenTo(this.collection, 'change:visible', this.show, this);
            this.$el.html('<p class="loading">Loading...</p>');
        },

        show: function(model, value, options) {
            // Ignore changes to visible that are false
            if (!value) return;

            if (this.previousView) {
                this.previousView.model.stopPolling();
                this.previousView.model.set('visible', false);
                this.previousView.remove();
            }
            model.startPolling();
            this.previousView = new this.childView({
                model: model
            });
            this.$el.html(this.previousView.el);
        }
    });


    var Link = Backbone.View.extend({
        tagName: 'li',

        template: _.template(systemLinkTemplate, null, {
            variable: 'data'
        }),

        events: {
            'click a': 'navigate'
        },

        initialize: function() {
            this.listenTo(this.model, 'change', this.render, this);
            this.listenTo(this.model, 'change:visible', this.toggle, this);

            this.$el.html(this.template(this.model.toJSON()));
        },

        render: function() {
            var icon = this.$('i');

            if (this.model.get('in_transition')) {
                icon.addClass('active');
            } else if (this.model.get('failed_last_transition')) {
                icon.addClass('failed');
            } else {
                icon.removeClass('active failed');
            }
        },

        navigate: function(event) {
            event.preventDefault();
            this.model.set('visible', true);
        },

        toggle: function(model, value, options) {
            this.$el.toggleClass('active', this.model.get('visible'));
        }
    });


    var SystemLinks = CollectionView.extend({
        tagName: 'ul',

        className: 'nav nav-list',

        childView: Link,

        initialize: function() {
            this.$el.html('<p class="loading">Loading...</p>');
            CollectionView.prototype.initialize.apply(this, arguments);
        }
    });


    STS.Models.System = SystemModel;
    STS.Models.Systems = SystemCollection;
    STS.Models.Transition = TransitionModel;
    STS.Models.Transitions = TransitionCollection;

    STS.Views.System = System;
    STS.Views.Systems = Systems;
    STS.Views.SystemLinks = SystemLinks;
    STS.Views.Transition = Transition;
    STS.Views.Transitions = Transitions;

})();
