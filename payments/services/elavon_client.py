import requests
from lxml import etree
from django.conf import settings


class ElavonClient:

    def __init__(self):
        config = settings.ELAVON_CONFIG

        self.account_id = config["merchant_id"]   # Cambiado nombre
        self.user_id = config["user_id"]
        self.pin = config["pin"]

        if config["is_demo"]:
            print ("DEMO")
            self.url = "https://api.demo.convergepay.com/VirtualMerchantDemo/processxml.do"
        else:
            self.url = "https://api.convergepay.com/VirtualMerchant/processxml.do"

    def _build_xml(self, data: dict):
        root = etree.Element("txn")

        # 1️⃣ Credenciales PRIMERO
        merchant = etree.SubElement(root, "ssl_merchant_id")
        merchant.text = str(self.account_id)

        user = etree.SubElement(root, "ssl_user_id")
        user.text = str(self.user_id)

        pin = etree.SubElement(root, "ssl_pin")
        pin.text = str(self.pin)

        # 2️⃣ Luego datos de transacción
        for key, value in data.items():
            if value is not None:
                elem = etree.SubElement(root, key)
                elem.text = str(value)

        return etree.tostring(
            root,
            encoding="UTF-8",
            xml_declaration=True
        ).decode("utf-8")

    def _parse_response(self, xml_response: bytes):
        root = etree.fromstring(xml_response)

        return {
            "result": root.findtext(".//ssl_result"),
            "message": root.findtext(".//ssl_result_message"),
            "txn_id": root.findtext(".//ssl_txn_id"),
            "approval_code": root.findtext(".//ssl_approval_code"),
            "amount": root.findtext(".//ssl_amount"),
            "txn_time": root.findtext(".//ssl_txn_time"),
            "account_balance": root.findtext(".//ssl_account_balance"),
        }

    def charge(self, amount, card_number, exp_date, cvv, invoice_number=None):

        if not invoice_number:
            invoice_number = str(uuid.uuid4())

        transaction_data = {
            "ssl_transaction_type": "ccsale",
            "ssl_amount": amount,
            "ssl_card_number": card_number,
            "ssl_exp_date": exp_date,
            "ssl_cvv2cvc2": cvv,
            "ssl_invoice_number": invoice_number,
            "ssl_partial_auth_indicator": "N",
        }

        xml_body = self._build_xml(transaction_data)

        print("XML ENVIADO:")
        print(xml_body)

        staticbody = '''<txn>
        <ssl_transaction_type>ccsale</ssl_transaction_type>
        <ssl_account_id>2735183</ssl_account_id>
        <ssl_user_id>admin</ssl_user_id>
        <ssl_pin>A1LURGFRIV5YYDE2S60LZ96SVRNN8HDZ8SB8RU3YA3N7XI37L2EZVPI5S8HZXTQQ</ssl_pin>
        <ssl_amount>1.50</ssl_amount>
        <ssl_card_number>4000000000000002</ssl_card_number>
        <ssl_exp_date>1230</ssl_exp_date>
        <ssl_cvv2cvc2_indicator>1</ssl_cvv2cvc2_indicator>
        <ssl_cvv2cvc2>123</ssl_cvv2cvc2>
        <ssl_invoice_number>INV001</ssl_invoice_number>
        </txn>'''

        response = requests.post(
            self.url,
            data={"xmldata": staticbody},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30
        )

        
        response.raise_for_status()

        print("STATUS CODE:", response.status_code)
        print("RAW RESPONSE:")
        print(response.text)

        return self._parse_response(response.content)