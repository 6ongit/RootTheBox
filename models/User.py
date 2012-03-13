'''
Created on Mar 12, 2012

@author: moloch
'''

from hashlib import md5, sha256
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import synonym, relationship, backref
from sqlalchemy.types import Unicode, Integer, Boolean
from models import dbsession
from models.Team import Team
from models.BaseGameObject import BaseObject

class User(BaseObject):
    """ User definition """

    user_name = Column(Unicode(64), unique=True, nullable=False)
    display_name = Column(Unicode(64), unique=True, nullable=False)
    team_id = Column(Integer, ForeignKey('team.id'))
    dirty = Column(Boolean)
    score_cache = Column(Integer)
    actions = relationship("Action", backref=backref("User", lazy="joined"), cascade="all, delete-orphan")
    permissions = relationship("Permission", backref=backref("User", lazy="joined"), cascade="all, delete-orphan")
    
    _password = Column('password', Unicode(128))
    password = synonym('_password', descriptor=property(
        lambda self: self._password,
        lambda self, password: setattr(self, '_password', self.__class__._hash_password(password))
    ))
    
    def __repr__(self):
        return ('<User - name: %s, display: %s, team_id: %d>' % (self.user_name, self.display_name, self.team_id)).encode('utf-8')

    def __unicode__(self):
        return self.display_name or self.user_name

    @property
    def permissions(self):
        """Return a set with all permissions granted to the user."""
        return dbsession.query(Permission).filter_by(user_id=self.id) #@UndefinedVariable

    @property
    def permissions_names(self):
        """Return a list with all permissions names granted to the user."""
        return [p.permission_name for p in self.permissions]
        
    def has_permission(self, permission):
        """Return True if ``permission`` is in permissions_names."""
        return True if permission in self.permissions_names else False

    @property
    def team_name(self):
        """ Return a list with all groups names the user is a member of """
        if self.team_id == None:
            return None
        else:
            team = dbsession.query(Team).filter_by(id=self.team_id).first() #@UndefinedVariable
            return team.team_name
    
    @property
    def score(self):
        if self.dirty:
            pass
        else:
            return self.score_cache
    
    @classmethod
    def by_user_name(cls, user_name):
        """ Return the user object whose user name is ``user_name`` """
        return dbsession.query(cls).filter_by(user_name=user_name).first() #@UndefinedVariable
    
    @classmethod
    def add_to_team(cls, team_name):
        team = dbsession.query(Team).filter_by(team_name=unicode(team_name)).first() #@UndefinedVariable
        cls.team_id = team.id
    
    @classmethod
    def _hash_password(cls, password):
        ''' Hashes the password using Md5/Sha256 :D '''
        if isinstance(password, unicode): 
            password = password.encode('utf-8')
        if cls.user_name == 'admin':
            shaHash = sha256()
            shaHash.update(password)
            shaHash.update(password + shaHash.hexdigest())
            password = shaHash.hexdigest()
        else:
            md5Hash = md5()
            md5Hash.update(password)
            password = md5Hash.hexdigest()
        if not isinstance(password, unicode): 
            password = password.decode('utf-8')
        return password

    def validate_password(self, password):
        """ Check the password against existing credentials """
        input_hash = md5()
        if isinstance(password, unicode): 
            password = password.encode('utf-8')
        input_hash.update(password)
        return self.password == input_hash.hexdigest()