"""
Comprehensive tests for task templates API endpoints.

Tests template creation, management, variable substitution, and usage tracking.
"""

import os
import pytest
import uuid
import httpx
from datetime import datetime, timezone


BASE_URL = os.getenv("BASE_URL", "http://0.0.0.0:8000")


async def create_user_and_login():
    """Helper function to create a user and get auth headers"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        email = f"test_{uuid.uuid4().hex[:12]}@test.com"
        password = "SecurePassword123!"

        # Create user
        signup_response = await client.post(
            "/v1/auth/signup", json={"email": email, "password": password}
        )
        assert signup_response.status_code == 201
        user_data = signup_response.json()

        # Login to get token
        login_response = await client.post(
            "/v1/auth/login", json={"email": email, "password": password}
        )
        assert login_response.status_code == 200
        token_data = login_response.json()

        return {
            "user": user_data,
            "headers": {"Authorization": f"Bearer {token_data['access_token']}"},
            "token": token_data['access_token']
        }


async def create_template(auth_headers, **kwargs):
    """Helper function to create a task template"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        default_data = {
            "name": f"Test Template {uuid.uuid4().hex[:8]}",
            "description": "Test template description",
            "category": "automation",
            "actions": [
                {"action_id": "1", "type": "screenshot", "params": {}}
            ],
            "variables": {"delay": "5"},
            "is_public": False
        }
        default_data.update(kwargs)

        response = await client.post(
            "/v1/templates/",
            json=default_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        return response.json()


@pytest.mark.asyncio
class TestTemplatesAPI:
    """Test task templates endpoints"""

    async def test_create_template_success(self):
        """Test creating a task template"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            payload = {
                "name": "Test Automation Template",
                "description": "Template for automated testing",
                "category": "testing",
                "actions": [
                    {"action_id": "1", "type": "screenshot", "params": {}},
                    {"action_id": "2", "type": "type_text",
                        "params": {"text": "{{user_input}}"}}
                ],
                "variables": {"user_input": "default text"},
                "is_public": False
            }

            response = await client.post(
                "/v1/templates/",
                json=payload,
                headers=auth_headers
            )

            assert response.status_code == 201
            data = response.json()

            assert "id" in data
            assert data["name"] == "Test Automation Template"
            assert data["description"] == "Template for automated testing"
            assert data["category"] == "testing"
            assert data["actions"] == payload["actions"]
            assert data["variables"] == payload["variables"]
            assert data["is_public"] is False
            assert data["usage_count"] == 0
            assert "created_at" in data

    async def test_create_public_template(self):
        """Test creating a public template"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            payload = {
                "name": "Public Template",
                "description": "A public template for everyone",
                "category": "shared",
                "actions": [
                    {"action_id": "1", "type": "screenshot", "params": {}}
                ],
                "variables": {"message": "Hello World"},
                "is_public": True
            }

            response = await client.post(
                "/v1/templates/",
                json=payload,
                headers=auth_headers
            )

            assert response.status_code == 201
            data = response.json()
            assert data["is_public"] is True

    async def test_create_template_missing_fields(self):
        """Test creating template with missing required fields"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Missing name
            payload = {
                "description": "Template without name",
                "category": "testing",
                "actions": [{"action_id": "1", "type": "screenshot", "params": {}}]
            }

            response = await client.post(
                "/v1/templates/",
                json=payload,
                headers=auth_headers
            )
            assert response.status_code == 422

            # Missing actions
            payload = {
                "name": "Template without actions",
                "description": "Template without actions",
                "category": "testing"
            }

            response = await client.post(
                "/v1/templates/",
                json=payload,
                headers=auth_headers
            )
            assert response.status_code == 422

    async def test_create_template_invalid_actions(self):
        """Test creating template with invalid actions format"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            payload = {
                "name": "Invalid Actions Template",
                "description": "Template with invalid actions",
                "category": "testing",
                "actions": "invalid_actions_format"  # Should be array
            }

            response = await client.post(
                "/v1/templates/",
                json=payload,
                headers=auth_headers
            )
            assert response.status_code == 422

    async def test_list_templates(self):
        """Test listing templates"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create test templates
            templates = []
            for i in range(3):
                template = await create_template(
                    auth_headers,
                    name=f"List Test Template {i}",
                    category="testing",
                    is_public=(i % 2 == 0)  # Alternate public/private
                )
                templates.append(template)

            response = await client.get(
                "/v1/templates/",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert len(data) >= 3  # At least our templates
            assert all("id" in template for template in data)
            assert all("name" in template for template in data)
            assert all("usage_count" in template for template in data)

    async def test_list_templates_with_filters(self):
        """Test listing templates with filters"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create templates with different categories
            automation_template = await create_template(
                auth_headers,
                name="Automation Template",
                category="automation",
                is_public=True
            )

            testing_template = await create_template(
                auth_headers,
                name="Testing Template",
                category="testing",
                is_public=False
            )

            # Test filter by category
            response = await client.get(
                "/v1/templates/?category=automation",
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert any(t["id"] == automation_template["id"] for t in data)

            # Test filter by is_public
            response = await client.get(
                "/v1/templates/?is_public=true",
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            public_templates = [t for t in data if t["is_public"]]
            assert len(public_templates) >= 1

            # Test filter by is_public=false (only user's private templates)
            response = await client.get(
                "/v1/templates/?is_public=false",
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert any(t["id"] == testing_template["id"] for t in data)

    async def test_get_template(self):
        """Test getting a specific template"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create template
            template = await create_template(
                auth_headers,
                name="Get Test Template",
                description="Template for get testing",
                category="testing"
            )

            response = await client.get(
                f"/v1/templates/{template['id']}",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert data["id"] == template["id"]
            assert data["name"] == "Get Test Template"
            assert data["description"] == "Template for get testing"
            assert data["category"] == "testing"
            assert "actions" in data
            assert "variables" in data

    async def test_get_template_not_found(self):
        """Test getting non-existent template"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            response = await client.get(
                f"/v1/templates/{uuid.uuid4()}",
                headers=auth_headers
            )

            assert response.status_code == 404
            assert "Template not found" in response.json()["detail"]

    async def test_update_template(self):
        """Test updating a template"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create template
            template = await create_template(
                auth_headers,
                name="Update Test Template",
                description="Original description",
                category="testing",
                is_public=False
            )

            update_payload = {
                "name": "Updated Template Name",
                "description": "Updated description",
                "category": "automation",
                "is_public": True
            }

            response = await client.put(
                f"/v1/templates/{template['id']}",
                json=update_payload,
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert data["name"] == "Updated Template Name"
            assert data["description"] == "Updated description"
            assert data["category"] == "automation"
            assert data["is_public"] is True

    async def test_update_template_not_found(self):
        """Test updating non-existent template"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            update_payload = {
                "name": "Non-existent Template"
            }

            response = await client.put(
                f"/v1/templates/{uuid.uuid4()}",
                json=update_payload,
                headers=auth_headers
            )

            assert response.status_code == 404
            assert "Template not found" in response.json()["detail"]

    async def test_delete_template(self):
        """Test deleting a template"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create template
            template = await create_template(
                auth_headers,
                name="Delete Test Template"
            )

            response = await client.delete(
                f"/v1/templates/{template['id']}",
                headers=auth_headers
            )

            assert response.status_code == 200
            assert response.json()["status"] == "deleted"

            # Verify template is deleted
            response = await client.get(
                f"/v1/templates/{template['id']}",
                headers=auth_headers
            )
            assert response.status_code == 404

    async def test_delete_template_not_found(self):
        """Test deleting non-existent template"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            response = await client.delete(
                f"/v1/templates/{uuid.uuid4()}",
                headers=auth_headers
            )

            assert response.status_code == 404
            assert "Template not found" in response.json()["detail"]

    async def test_template_variable_substitution(self):
        """Test template variable substitution"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create template with variables
            template = await create_template(
                auth_headers,
                name="Variable Template",
                actions=[
                    {"action_id": "1", "type": "type_text",
                        "params": {"text": "{{message}}"}},
                    {"action_id": "2", "type": "click", "params": {
                        "x": "{{x_coord}}", "y": "{{y_coord}}"}}
                ],
                variables={"message": "Hello",
                           "x_coord": "100", "y_coord": "200"}
            )

            # Test variable substitution endpoint
            substitution_payload = {
                "variables": {
                    "message": "Hello World!",
                    "x_coord": "150",
                    "y_coord": "250"
                }
            }

            response = await client.post(
                f"/v1/templates/{template['id']}/substitute",
                json=substitution_payload,
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            # Check that variables were substituted
            assert data["actions"][0]["params"]["text"] == "Hello World!"
            assert data["actions"][1]["params"]["x"] == "150"
            assert data["actions"][1]["params"]["y"] == "250"

    async def test_template_usage_tracking(self):
        """Test template usage count tracking"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create template
            template = await create_template(
                auth_headers,
                name="Usage Tracking Template"
            )

            # Get initial usage count
            response = await client.get(
                f"/v1/templates/{template['id']}",
                headers=auth_headers
            )
            initial_count = response.json()["usage_count"]

            # Use template (simulate usage)
            response = await client.post(
                f"/v1/templates/{template['id']}/use",
                headers=auth_headers
            )

            assert response.status_code == 200

            # Check usage count increased
            response = await client.get(
                f"/v1/templates/{template['id']}",
                headers=auth_headers
            )
            new_count = response.json()["usage_count"]
            assert new_count == initial_count + 1

    async def test_template_categories(self):
        """Test template category functionality"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create templates in different categories
            categories = ["automation", "testing", "productivity", "custom"]

            for category in categories:
                await create_template(
                    auth_headers,
                    name=f"{category.title()} Template",
                    category=category
                )

            # Get categories endpoint
            response = await client.get(
                "/v1/templates/categories",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            # Should include our categories
            returned_categories = [cat["name"] for cat in data]
            for category in categories:
                assert category in returned_categories

    async def test_template_statistics(self):
        """Test template statistics endpoint"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create templates with usage
            popular_template = await create_template(
                auth_headers,
                name="Popular Template",
                is_public=True
            )

            # Simulate usage
            for _ in range(5):
                await client.post(
                    f"/v1/templates/{popular_template['id']}/use",
                    headers=auth_headers
                )

            # Get statistics
            response = await client.get(
                "/v1/templates/statistics",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert "total_templates" in data
            assert "public_templates" in data
            assert "private_templates" in data
            assert "most_used" in data
            assert data["total_templates"] >= 1

    async def test_unauthorized_access(self):
        """Test unauthorized access to templates endpoints"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            endpoints = [
                ("POST", "/v1/templates/"),
                ("GET", "/v1/templates/"),
                ("GET", f"/v1/templates/{uuid.uuid4()}"),
                ("PUT", f"/v1/templates/{uuid.uuid4()}"),
                ("DELETE", f"/v1/templates/{uuid.uuid4()}"),
                ("POST", f"/v1/templates/{uuid.uuid4()}/substitute"),
                ("POST", f"/v1/templates/{uuid.uuid4()}/use"),
                ("GET", "/v1/templates/categories"),
                ("GET", "/v1/templates/statistics"),
            ]

            for method, url in endpoints:
                response = await client.request(method, url)
                assert response.status_code == 401

    async def test_cross_user_template_access(self):
        """Test cross-user template access permissions"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create first user and private template
            auth_data1 = await create_user_and_login()
            auth_headers1 = auth_data1["headers"]

            private_template = await create_template(
                auth_headers1,
                name="Private Template",
                is_public=False
            )

            public_template = await create_template(
                auth_headers1,
                name="Public Template",
                is_public=True
            )

            # Create second user
            auth_data2 = await create_user_and_login()
            auth_headers2 = auth_data2["headers"]

            # Second user should not see private template
            response = await client.get(
                f"/v1/templates/{private_template['id']}",
                headers=auth_headers2
            )
            assert response.status_code == 404

            # Second user should see public template
            response = await client.get(
                f"/v1/templates/{public_template['id']}",
                headers=auth_headers2
            )
            assert response.status_code == 200

            # Second user cannot update first user's template
            response = await client.put(
                f"/v1/templates/{public_template['id']}",
                json={"name": "Hacked Template"},
                headers=auth_headers2
            )
            assert response.status_code == 403  # Forbidden

            # Second user cannot delete first user's template
            response = await client.delete(
                f"/v1/templates/{private_template['id']}",
                headers=auth_headers2
            )
            assert response.status_code == 404


@pytest.mark.asyncio
class TestTemplatesIntegration:
    """Integration tests for templates"""

    async def test_template_with_complex_variables(self):
        """Test templates with complex variable structures"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create template with nested variables
            template = await create_template(
                auth_headers,
                name="Complex Variables Template",
                actions=[
                    {
                        "action_id": "1",
                        "type": "complex_action",
                        "params": {
                            "config": {
                                "url": "{{base_url}}/{{endpoint}}",
                                "method": "{{http_method}}",
                                "headers": {
                                    "Authorization": "Bearer {{token}}",
                                    "Content-Type": "{{content_type}}"
                                }
                            }
                        }
                    }
                ],
                variables={
                    "base_url": "https://api.example.com",
                    "endpoint": "users",
                    "http_method": "GET",
                    "token": "default_token",
                    "content_type": "application/json"
                }
            )

            # Test substitution with complex variables
            substitution_payload = {
                "variables": {
                    "base_url": "https://api.test.com",
                    "endpoint": "posts",
                    "http_method": "POST",
                    "token": "test_token_123",
                    "content_type": "application/json"
                }
            }

            response = await client.post(
                f"/v1/templates/{template['id']}/substitute",
                json=substitution_payload,
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            config = data["actions"][0]["params"]["config"]
            assert config["url"] == "https://api.test.com/posts"
            assert config["method"] == "POST"
            assert config["headers"]["Authorization"] == "Bearer test_token_123"

    async def test_template_performance_with_many_templates(self):
        """Test performance with many templates"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create many templates
            templates = []
            for i in range(20):  # Reduced from 50 for faster testing
                template = await create_template(
                    auth_headers,
                    name=f"Performance Template {i}",
                    category=f"category_{i % 5}",  # 5 different categories
                    is_public=(i % 3 == 0)  # Some public, some private
                )
                templates.append(template)

            # Test listing performance
            response = await client.get(
                "/v1/templates/?limit=50",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) >= 20

            # Test category filtering performance
            response = await client.get(
                "/v1/templates/?category=category_0",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) >= 4  # Should have 4 templates in category_0

    async def test_template_concurrent_usage(self):
        """Test concurrent template usage"""
        import asyncio

        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create template
            template = await create_template(
                auth_headers,
                name="Concurrent Usage Template"
            )

            # Concurrent usage operations
            async def use_template():
                return await client.post(
                    f"/v1/templates/{template['id']}/use",
                    headers=auth_headers
                )

            # Run multiple usage requests concurrently
            responses = await asyncio.gather(*[use_template() for _ in range(5)])

            # All requests should succeed
            assert all(r.status_code == 200 for r in responses)

            # Check final usage count
            response = await client.get(
                f"/v1/templates/{template['id']}",
                headers=auth_headers
            )
            assert response.status_code == 200
            final_count = response.json()["usage_count"]
            assert final_count == 5  # Should have been incremented 5 times

    async def test_template_export_import(self):
        """Test template export and import functionality"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create template
            original_template = await create_template(
                auth_headers,
                name="Export Test Template",
                description="Template for export testing",
                category="testing",
                actions=[
                    {"action_id": "1", "type": "screenshot", "params": {}},
                    {"action_id": "2", "type": "type_text",
                        "params": {"text": "{{message}}"}}
                ],
                variables={"message": "Hello Export!"}
            )

            # Export template
            response = await client.get(
                f"/v1/templates/{original_template['id']}/export",
                headers=auth_headers
            )

            assert response.status_code == 200
            exported_data = response.json()

            # Verify export data structure
            assert "name" in exported_data
            assert "description" in exported_data
            assert "actions" in exported_data
            assert "variables" in exported_data
            assert "id" not in exported_data  # ID should not be exported

            # Import as new template
            import_payload = exported_data.copy()
            import_payload["name"] = "Imported Template"

            response = await client.post(
                "/v1/templates/import",
                json=import_payload,
                headers=auth_headers
            )

            assert response.status_code == 201
            imported_template = response.json()

            # Verify imported template
            assert imported_template["name"] == "Imported Template"
            assert imported_template["description"] == exported_data["description"]
            assert imported_template["actions"] == exported_data["actions"]
            assert imported_template["variables"] == exported_data["variables"]
            # Should have new ID
            assert imported_template["id"] != original_template["id"]
