# src/gateway/handlers/enable_fact_pod_handler.py
import logging
from typing import Dict, Any
from fastmcp.server import FastMCP

from gateway.services.fact_pod_service import FactPodOAuthService
from gateway.clients.openid_client import HttpOpenIDClient
from gateway.handlers.base_handler import BaseHandler
from gateway.clients.http_client import AsyncHTTPClient
from gateway.exceptions import (
    GatewayError,
    FactPodServiceError,
    RepositoryError,
)

logger = logging.getLogger(__name__)


class EnableFactPodHandler(BaseHandler):
    def __init__(self, mcp_instance: FastMCP):
        """
        Initialize the handler with the MCP instance.

        Args:
            mcp_instance: The FastMCP instance to use for registration
        """
        super().__init__(mcp_instance)
        # Initialize dependencies
        self.fact_pod_service = FactPodOAuthService(
            openid_client=HttpOpenIDClient(AsyncHTTPClient()),
            repository=self.repository
        )

    async def tool_method(self, user_id: str, site: str) -> Dict[str, Any]:
        """
        Enable a Fact Pod for a user on a site.

        Args:
            user_id: The ID of the user
            site: The domain of the site to enable the fact pod for

        Returns:
            Dict containing status, message, and auth URL if successful
        """
        try:
            return await self.fact_pod_service.enable_fact_pod(site, user_id)
        except FactPodServiceError as e:
            logger.error(f"Fact Pod service error: {str(e)}")
            return {
                "status": "error",
                "message": f"Service error: {str(e)}",
                "auth_url": None
            }
        except RepositoryError as e:
            logger.error(f"Repository error: {str(e)}")
            return {
                "status": "error",
                "message": f"Database error: {str(e)}",
                "auth_url": None
            }
        except GatewayError as e:
            logger.error(f"Gateway error: {str(e)}")
            error_message = str(e)

            # Special case for already enabled fact pods
            if "already enabled for user" in error_message:
                return {
                    "status": "already_enabled",
                    "message": f"Fact Pod for {site} is already enabled for user {user_id}",
                    "auth_url": None
                }

            return {
                "status": "error",
                "message": f"Gateway error: {str(e)}",
                "auth_url": None
            }
        except Exception as e:
            logger.error(
                f"Unexpected error in EnableFactPodHandler: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"An unexpected error occurred: {str(e)}",
                "auth_url": None
            }
