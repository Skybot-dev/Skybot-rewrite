import logging
# import statuspageio
from loguru import logger
# from utils.util import get_config

class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def init_logging():
    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.INFO)
    discord_logger.addHandler(InterceptHandler())
    slash_logger = logging.getLogger("discord_slash")
    slash_logger.setLevel(logging.INFO)
    slash_logger.addHandler(InterceptHandler())

    logger.add("skybot.log", enqueue=True, level="INFO")



# class Componenets():
#     CORE = "f3wr6lvvv4wr"
#     HELP = "69x154c10cy9"
#     CONFIG = "z56sbn5tdzq0"
#     DICT = {"f3wr6lvvv4wr" : "CORE", "69x154c10cy9" : "HELP", "z56sbn5tdzq0" : "CONFIG"}

# class Status():
#     OPERATIONAL = "operational"
#     MAINTENANCE = "under_maintenance"
#     DEGRADED_PERFORMANCE = "degraded_performance"
#     PARTIAL_OUTAGE = "partial_outage"
#     MAJOR_OUTAGE = "major_outage"

# def init_statuspage():
#     statuspage = statuspageio.Client(api_key=get_config()["statuspage"]["api_key"], page_id=get_config()["statuspage"]["page_id"], organization_id="pleasenoerror")
#     return statuspage

# async def set_status(statuspage : statuspageio.Client, component_id : str, status : str):
#     statuspage.components.update(component_id, status=status)
#     logger.info(f"{Componenets.DICT[component_id]} component status set to {status}!")

# async def create_incident(statuspage : statuspageio.Client, name : str, components : list):
#     statuspage.incidents.create(name=name, components=components)
#     logger.warning(f"Created new incident with the name {name} for {Componenets.DICT[components[0]]} !")




    




