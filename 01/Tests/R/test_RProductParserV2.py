import json
import os
from http import HTTPStatus
from unittest.mock import MagicMock

from bson import ObjectId

from Middleware.Context import Context
from Model.enums import POS
from Model.operationReport import OperationReport, OperationReportStatus
from Model.product import ProductSyncSettings
from POSSystems.R.RAPI import RAPI
from Tests.DataGenerator import BaseDataGenerator
from Tests.integration.utils import getlogger

logger = getlogger(__name__, "ERROR")
settings = dict(
    r=dict(
        useWebOrderMenu=True,
        establishment="testEstablishment",
        clientId="someClientId",
    )
)


def test_parseWeMenu(testApp, testClient, database):
    dataGenerator = BaseDataGenerator()
    headers = {"Correlation-Id": "someValue"}
    currentDir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(currentDir, "mockData/webordersMenu.json")) as f:
        rawMenu = json.load(f)
    with testApp.test_request_context():
        account = dataGenerator.createAccount()
        database.insertAccount(account)

        channelLink = dataGenerator.createChannelLink(posSettings=settings)
        database.insertChannelLinks([channelLink])

        objId = ObjectId()
        location = dataGenerator.createLocation(
            _id=objId,
            name="R location",
            account=account.oid,
            posSystemId=POS.r,
            channelLinks=[channelLink.oid],
            posSettings=settings,
        )
        database.insertLocations([location])
        operationReport = OperationReport(location=objId)
        database.saveOperationReport(operationReport)
        api = RAPI(location)
        mockResponse = MagicMock()
        mockResponse.status = HTTPStatus.CREATED
        mockResponse.return_value.headers.get.return_value = "someValue"
        # check that we do not have products
        assert database.myDB.products.find({"location": location.oid})
        api._callPOSAPI = mockResponse
        with Context(operationReport=operationReport):
            productSyncInfo = api.getProductSyncInfo(ProductSyncSettings())
            database.saveOperationReport(operationReport)
            assert productSyncInfo.callback
            # for callback call we have an empty products and categories
            assert productSyncInfo.products == productSyncInfo.categories == []
            assert operationReport.operationStatus == OperationReportStatus.AWAIT
            assert "correlationId" in operationReport.properties
            assert "defaultTax" in operationReport.properties

        # invalid operation report id
        invalidResponse1 = testClient.post(f"/r/menu/{ObjectId()}")
        assert invalidResponse1.json == {"error": "Cannot continue with product sync"}
        # missing or mismatch correlationId
        invalidResponse2 = testClient.post(f"/r/menu/{operationReport.oid}")
        assert invalidResponse2.json == {
            "error": "R menu sync webhook: response correlation-id mismatch with request correlation-id. Sync aborted"
        }
        # valid response
        testClient.post(f"/r/menu/{operationReport.oid}", headers=headers, json=rawMenu)

        # refresh operation report after sync
        operationReport = database.getOperationReport(operationReport.oid)

        assert operationReport.operationStatus == OperationReportStatus.SUCCESS

        assert operationReport.productSync
