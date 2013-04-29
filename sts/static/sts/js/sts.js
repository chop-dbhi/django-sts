(function() {

    this.STS = STS = {
        Models: {},
        Views: {}
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
        '<div class=page-header>',
            '<h2 class=name><%= data.name %></h2>',
        '</div>',
        '<p class=meta><%= data.created %> &middot; <%= data.modified %></p>',
        '<div class=transitions></div>'
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

    var SystemModel = Backbone.Model.extend({
        options: {
            poll: true,
            interval: 5000
        },

        url: function() {
            return this.get('url');
        },

        initialize: function(attrs, options) {
            _.extend(this.options, _.pick(options, ['poll', 'interval']));
            this.transitions = new TransitionCollection;
            this.fetch({parse: true});
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
        model: function(attrs, options) {
            options.poll = false;
            return new SystemModel(attrs, options);
        },

        options: {
            poll: true,
            interval: 5000
        },

        initialize: function() {
            this.fetch();
            if (this.options.poll) this.startPolling();
        },

        startPolling: function() {
            this.stopPolling();

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

    var Transitions = Backbone.View.extend({
        childView: Transition,

        initialize: function() {
            this.listenTo(this.collection, 'reset', this.reset, this)
            this.listenTo(this.collection, 'add', this.add, this)
        },

        render: function() {
            return this;
        },

        reset: function(collection, options) {
            var _this = this;
            collection.each(function(model) {
                _this.add(model, collection, options);
            });
        },

        add: function(model, collection, options) {
            var view = new this.childView({
                model: model
            });
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

        initialize: function(options) {
            this.$el.html(this.template(this.model.toJSON()));

            this.$name = this.$('.name');
            this.$meta = this.$('.meta');
            this.$transitions = this.$('.transitions');

            this.listenTo(this.model, 'change', this.render, this);

            this.transitions = new Transitions(_.defaults({
                el: this.$transitions,
                collection: this.model.transitions
            }, options));

        },

        render: function() {
            this.$name.text(this.model.get('name'));

            var created = renderTime(this.model.get('created')),
                modified = renderTime(this.model.get('modified'));

            this.$meta.html('created: ' + created + ' &middot; ' + 'modified: ' + modified);
        }
    });


    var Link = Backbone.View.extend({
        tagName: 'li',

        render: function() {
            this.$el.html('<a href="' + this.model.get('url') + '">' + this.model.get('name') + '</a>');
        }
    });


    var SystemLinks = Backbone.View.extend({
        tagName: 'ul',

        className: 'nav nav-list',

        childView: Link,

        initialize: function() {
            this.listenTo(this.collection, 'reset', this.reset, this);
            this.listenTo(this.collection, 'add', this.add, this);
        },

        render: function() {
            return this;
        },

        reset: function(collection, options) {
            var _this = this;
            collection.each(function(model) {
                _this.add(model, collection, options);
            });
        },

        add: function(model, collection, options) {
            var view = new this.childView({
                model: model
            });
            view.render();
            this.$el.append(view.el);
            return view;
        }
    });


    STS.Models.System = SystemModel;
    STS.Models.Systems = SystemCollection;
    STS.Models.Transition = TransitionModel;
    STS.Models.Transitions = TransitionCollection;

    STS.Views.System = System;
    STS.Views.SystemLinks = SystemLinks;
    STS.Views.Transition = Transition;
    STS.Views.Transitions = Transitions;

})();
