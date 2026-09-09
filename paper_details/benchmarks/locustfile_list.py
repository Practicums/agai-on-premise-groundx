from locust import HttpUser, task, between
import random
import string
import os


def random_string(length=10):
    """Generate a random string of fixed length."""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))


class UploadTester(HttpUser):
    """Simple load test for the upload endpoint only."""

    wait_time = between(0.1, 0.5)
    
    SMALL_BUFFER = os.urandom(10 * 1024)    # 10 KB
    MEDIUM_BUFFER = os.urandom(100 * 1024)  # 100 KB
    LARGE_BUFFER = os.urandom(1024 * 1024)  # 1 MB
    XLARGE_BUFFER = os.urandom(10 * 1024 * 1024)  # 10 MB

    @task
    def upload_document(self):
        """Test the document upload endpoint."""
        # Determine how many files to upload (1-5)
        num_files = random.randint(1, 5)
        # file list with accepted file types
        file_types = [
            (".pdf", "application/pdf"), 
            (".xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            (".pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
            (".txt", "text/plain")
        ]

        # create a list of files to upload with random file types
        files = {}

        for i in range(num_files):
            # choose a file type and its extension
            file_ext, file_type = random.choice(file_types)

            # create a random file name
            filename = f"test_{random_string(5)}{file_ext}"
            print("generate filename:", filename)
            # generate random content for the file
            size_choice = random.choice(['small', 'medium', 'large', 'xlarge'])
            if size_choice == 'small':
                file_content = self.SMALL_BUFFER
            elif size_choice == 'medium':
                file_content = self.MEDIUM_BUFFER
            elif size_choice == 'large':
                file_content = self.LARGE_BUFFER
            elif size_choice == 'xlarge':
                file_content = self.XLARGE_BUFFER

            # add the file to the files dictionary
            files[f"file-{i}"] = (filename, file_content, file_type)
        print("uploading files")
        # Send the files to the upload endpoint
        self.client.post("upload/", files=files)
        print("uploading files done")


class ListTester(HttpUser):
    """Simple load test for the document listing endpoint only."""
    
    @task
    def list_documents(self):
        """Test the document listing endpoint."""
        self.client.get("/api/documents/list")


class XRayTester(HttpUser):
    """Simple load test for the X-Ray data endpoint only."""
    xray_urls = ["https://mock-groundx.example.com/documents/123/xray.json"]
    
    @task
    def get_xray_data(self):
        """Test the X-Ray data endpoint."""
        xray_url = random.choice(self.xray_urls)
        self.client.get("/api/documents/xray", params={"xrayUrl": xray_url})


class ImageTester(HttpUser):
    """Simple load test for the image proxy endpoint only."""
    wait_time = between(0.1, 1)
    
    @task
    def proxy_image(self):
        """Test the image proxy endpoint."""
        image_url = "https://mock-groundx.example.com/images/test.jpg"
        self.client.get("/api/images/proxy", params={"url": image_url})


class DeleteTester(HttpUser):
    """Simple load test for the document deletion endpoint only."""
    
    @task
    def delete_document(self):
        """Test the document deletion endpoint."""
        self.client.post("/api/documents/delete", json={"documentIds": [random.randint(1, 100) for _ in range(random.randint(1, 5))]})