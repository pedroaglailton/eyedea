# importações
import os
import json
from pathlib import Path
from typing import Optional
import requests

# classe MmrApiClient
class MmrApiClient:
    def __init__(self, server_url):
        """
        Initialize by storing url
        :param server_url: address of MMR web server, e.g. https://cloud.eyedea.cz/.
        """
        self.server_url = server_url

    def info(self, email: str, password: str):
        """
        Query web server status information.
        :param email: Your login email as created at 'https://cloud.eyedea.cz/api/VCL/rest'.
        :param password: The password you received to the specified email.
        :return: JSON response structure
        """
        payload = {"email": email, "password": password}
        r = requests.post(self.server_url + "api/v2/serverSystemInfo", data=payload)

        if r.status_code != 200:
            raise ValueError(f"Server returned error code {r.status_code}")

        info_result = json.loads(r.content.decode("utf-8"))
        return info_result

    def run(
            self,
            email: str,
            password: str,
            image_path: Path,
            center_x: Optional[float] = None,
            center_y: Optional[float] = None,
            scale_pixel_per_meter: Optional[float] = None,
            inplane_rotation_angle: Optional[float] = None,
    ):
        """
        Send image file to server for processing. If all optional inputs are set, the web server won't run
        detection, but will only process the selected vehicle.
        :param email: Your login email as created at 'https://cloud.eyedea.cz/api/VCL/rest'.
        :param password: The password you received to the specified email.
        :param image_path: Path to the image.
        :param center_x: Center of car plate, column coordinate. Optional.
        :param center_y: Center of car plate, row coordinate. Optional.
        :param scale_pixel_per_meter: How many pixels there are per one meter on the face of the plate. Optional.
        :param inplane_rotation_angle: Angle of rotation of the plate. Optional.
        :return: JSON response structure
        """
        payload = {"email": email, "password": password}

        if all((center_x, center_y, scale_pixel_per_meter, inplane_rotation_angle)):
            lp_detection = [
                {
                    "center": {"x": center_x, "y": center_y},
                    "angle": inplane_rotation_angle,
                    "scalePPM": scale_pixel_per_meter,
                }
            ]
            json_lp_detection = json.dumps(lp_detection)
            payload["lpDetection"] = json_lp_detection

        with open(str(image_path), "rb") as f:
            file_buffer = f.read()

        files = {"file": (str(image_path), file_buffer)}

        r = requests.post(self.server_url + "api/v2/mmrdetect", data=payload, files=files)

        if r.status_code != 200:
            raise ValueError(f"Server returned error code {r.status_code}")

        classification = json.loads(r.content.decode("utf-8"))
        return classification

# variáveis
IMAGE_FOLDER = Path("cra")
NET_ADDRESS = "https://cloud.eyedea.cz/"
EMAIL = " "
PASSWORD = " "
OUTPUT_FILE = "output.json"

if not all((IMAGE_FOLDER, EMAIL, PASSWORD)):
    raise ValueError("You must set you MMR web demo account information and image path prior to running this script.")

# instanciando a classe MmrApiClient
client = MmrApiClient(NET_ADDRESS)

# colhendo informações do servidor
info = client.info(EMAIL, PASSWORD)

# fazendo a varredura das imagens da pasta e processando cada uma
image_paths = [os.path.join(IMAGE_FOLDER, f) for f in os.listdir(IMAGE_FOLDER) if f.endswith(".jpg")]
results = []
for image_path in image_paths:
    response = client.run(EMAIL, PASSWORD, Path(image_path))
    results.append(response)

# salvar os resultados em um arquivo JSON
with open(OUTPUT_FILE, "w") as f:
    json.dump(results, f)

#Define as chaves que queremos extrair do arquivo JSON vindo Servidor, voce escolhe a categoria que vai ser util.
keys_to_extract = ["color", "ocrText", "category", "make", "view"]

# Define o nome do arquivo de entrada e do arquivo de saída
input_file =  Path(OUTPUT_FILE)
output_file2 = "resultado.json"

# Lê o arquivo de entrada
with open(input_file, "r") as f:
    data = json.load(f)

# Extrai apenas as informações desejadas que voce escolheu
extracted_data = []
for item in data:
    tags = item.get("tags", [])
    for tag in tags:
        extracted_item = {}
        extracted_item["color"] = tag.get("mmrResult", {}).get("color", "")
        extracted_item["ocrText"] = tag.get("anprResult", {}).get("ocrText", "")
        #extracted_item["category"] = tag.get("mmrResult", {}).get("category", "")
        #extracted_item["make"] = ""
        #extracted_item["view"] = tag.get("mmrResult", {}).get("view", "")
        extracted_data.append(extracted_item)

# Salva as informações extraídas em um novo arquivo JSON
with open(output_file2, "w") as f:
    json.dump(extracted_data, f)
	# O que fiz foi so uma implementação ao codigo original
