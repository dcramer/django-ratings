
from south.db import db
from django.db import models
from djangoratings.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'Score'
        db.create_table('djangoratings_score', (
            ('id', orm['djangoratings.Score:id']),
            ('content_type', orm['djangoratings.Score:content_type']),
            ('object_id', orm['djangoratings.Score:object_id']),
            ('key', orm['djangoratings.Score:key']),
            ('score', orm['djangoratings.Score:score']),
            ('votes', orm['djangoratings.Score:votes']),
        ))
        db.send_create_signal('djangoratings', ['Score'])
        
        # Adding model 'Vote'
        db.create_table('djangoratings_vote', (
            ('id', orm['djangoratings.Vote:id']),
            ('content_type', orm['djangoratings.Vote:content_type']),
            ('object_id', orm['djangoratings.Vote:object_id']),
            ('key', orm['djangoratings.Vote:key']),
            ('score', orm['djangoratings.Vote:score']),
            ('user', orm['djangoratings.Vote:user']),
            ('ip_address', orm['djangoratings.Vote:ip_address']),
            ('date_added', orm['djangoratings.Vote:date_added']),
            ('date_changed', orm['djangoratings.Vote:date_changed']),
        ))
        db.send_create_signal('djangoratings', ['Vote'])
        
        # Creating unique_together for [content_type, object_id, key, user, ip_address] on Vote.
        db.create_unique('djangoratings_vote', ['content_type_id', 'object_id', 'key', 'user_id', 'ip_address'])
        
        # Creating unique_together for [content_type, object_id, key] on Score.
        db.create_unique('djangoratings_score', ['content_type_id', 'object_id', 'key'])
        
    
    
    def backwards(self, orm):
        
        # Deleting unique_together for [content_type, object_id, key] on Score.
        db.delete_unique('djangoratings_score', ['content_type_id', 'object_id', 'key'])
        
        # Deleting unique_together for [content_type, object_id, key, user, ip_address] on Vote.
        db.delete_unique('djangoratings_vote', ['content_type_id', 'object_id', 'key', 'user_id', 'ip_address'])
        
        # Deleting model 'Score'
        db.delete_table('djangoratings_score')
        
        # Deleting model 'Vote'
        db.delete_table('djangoratings_vote')
        
    
    
    models = {
        'auth.group': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True', 'null': 'True', 'blank': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'djangoratings.score': {
            'Meta': {'unique_together': "(('content_type', 'object_id', 'key'),)"},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'score': ('django.db.models.fields.IntegerField', [], {}),
            'votes': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'djangoratings.vote': {
            'Meta': {'unique_together': "(('content_type', 'object_id', 'key', 'user', 'ip_address'),)"},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'votes'", 'to': "orm['contenttypes.ContentType']"}),
            'date_added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'date_changed': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'score': ('django.db.models.fields.IntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'votes'", 'null': 'True', 'to': "orm['auth.User']"})
        }
    }
    
    complete_apps = ['djangoratings']
