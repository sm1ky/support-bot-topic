from . import command
from . import message
from . import callback_query


routers = [
    command.router,
    command.router_id,
    message.router,
    callback_query.router,
]
