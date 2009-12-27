class InvalidRating(ValueError): pass
class AuthRequired(TypeError): pass
class CannotChangeVote(Exception): pass
class IPLimitReached(Exception): pass