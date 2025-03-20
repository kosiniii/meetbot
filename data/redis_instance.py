from data.redis_core import Custom_redis

__redis_users__ = Custom_redis(key='active_users', data=list)
__redis_room__ = Custom_redis(key='rooms', data=dict) 