import time
import json
import AWSIoTPythonSDK.MQTTLib as AWSIoTPyMQTT
import random
import datetime
import os
import boto3
# Define ENDPOINT, TOPIC, RELATIVE DIRECTORY for CERTIFICATE AND KEYS
ENDPOINT = "a1jsvrjefqwiua-ats.iot.us-east-1.amazonaws.com"
PATH_TO_CERT = "..\\config"


spr_list_with_obj={}

class AWS():
    def __init__(self, client, certificate, private_key,root_path,sprinkler_id,sprinkler_state,TOPIC):
        self.client_id = client
        self.device_id = client
        self.cert_path = PATH_TO_CERT + "\\" + certificate
        self.pvt_key_path = PATH_TO_CERT + "\\" + private_key
        self.root_path = PATH_TO_CERT + "\\" + root_path
        self.myAWSIoTMQTTClient = AWSIoTPyMQTT.AWSIoTMQTTClient(self.client_id)
        self.myAWSIoTMQTTClient.configureEndpoint(ENDPOINT, 8883)
        self.myAWSIoTMQTTClient.configureCredentials(self.root_path, self.pvt_key_path, self.cert_path)
        self.sprinkler_state = sprinkler_state
        self.tem_value=80
        self.topic=TOPIC
        self.sprinkler_id=sprinkler_id
        # Initialize the dynamo client
        self.dynamodb_client = boto3.client('dynamodb')
        li(self.sprinkler_id,self.device_id)
        spr_list_with_obj[self.sprinkler_id][self.device_id]=False

    def _connect(self):
        self.myAWSIoTMQTTClient.connect()

    def _simulate_soil_moisture_change(self, current_value, sprinkle_id):
        # Simulate gradual progression of soil moisture based on sprinkler state

        if all(val is False for val in spr_list_with_obj[sprinkle_id].values()):
            # If sprinkler is off, gradually decrease soil moisture towards dry level
            self.tem_value=max(self.tem_value - random.uniform(0.5, 2.0), 60.0)
            return  self.tem_value # Adjusted upper limit to 40

        else:
            # If sprinkler is on, gradually increase soil moisture towards normal level
            self.tem_value=min(self.tem_value + random.uniform(0.5, 3.0), 80.0)
            return self.tem_value  # Adjusted upper limit to 80

    def publish(self):
        self._connect()
        while True:
            # Simulate updating sprinkler state randomly for each iteration
            # li(self.sprinkler_id,self.device_id)
            sprinklestate(self.sprinkler_id, self.device_id, self.tem_value)
            self._simulate_soil_moisture_change(self.tem_value,self.sprinkler_id)

            # Simulate soil moisture change based on sprinkler state
            current_value = self._simulate_soil_moisture_change(self.tem_value,self.sprinkler_id)
            message = {}
            timestamp = str(datetime.datetime.now())
            message['deviceid'] = self.device_id
            message['timestamp'] = timestamp
            message['datatype'] = 'Soil_Moisture'
            message['value'] = round(current_value, 1)
            messageJson = json.dumps(message)
            self.myAWSIoTMQTTClient.publish(self.topic, messageJson, 1)

            if current_value == 60:
                spr_list_with_obj[self.sprinkler_id][self.device_id] = not (spr_list_with_obj[self.sprinkler_id][self.device_id])

            print("Published: '" + json.dumps(message) + "' to the topic: " + self.topic +" "+ self.sprinkler_id + " state is " + str(spr_list_with_obj[self.sprinkler_id][self.device_id]))

            # # Route message to S3 based on device ID
            # s3_folder = f'soil_sensors/{self.device_id}'
            # s3_key = f'{s3_folder}/{timestamp}.json'
            # self.s3_client.put_object(Bucket='your_s3_bucket_name', Key=s3_key, Body=messageJson)

            break

    def disconnect(self):
        self.myAWSIoTMQTTClient.disconnect()


def li(sprink_def_id,sensor_id):
    if sprink_def_id not in spr_list_with_obj:
        spr_list_with_obj[sprink_def_id]={}


def sprinklestate(sprink_def_id,sensor_id,tem_value):
    if tem_value == 60:
        spr_list_with_obj[sprink_def_id] = {key: True for key in spr_list_with_obj[sprink_def_id]}

    if tem_value == 80:
        spr_list_with_obj[sprink_def_id][sensor_id]= False

class AWS_Sprinkler():
    def __init__(self, certificate, private_key,root_path,sprinkler_id,TOPIC):
        self.sprinkler_id = sprinkler_id
        self.cert_path = PATH_TO_CERT + "\\" + certificate
        self.pvt_key_path = PATH_TO_CERT + "\\" + private_key
        self.root_path = PATH_TO_CERT + "\\" + root_path
        self.myAWSIoTMQTTClient = AWSIoTPyMQTT.AWSIoTMQTTClient(self.sprinkler_id)
        self.myAWSIoTMQTTClient.configureEndpoint(ENDPOINT, 8883)
        self.myAWSIoTMQTTClient.configureCredentials(self.root_path, self.pvt_key_path, self.cert_path)
        self.topic=TOPIC
        # Initialize the dynamo client
        self.dynamodb_client = boto3.client('dynamodb')

    def _connect(self):
        self.myAWSIoTMQTTClient.connect()
    def disconnect(self):
        self.myAWSIoTMQTTClient.disconnect()
    def sprinkler_state_decide(self):
        if any(spr_list_with_obj[self.sprinkler_id].values()):
            return True
        else:
            return False
    def publish(self):
        self._connect()
        while True:
            message = {}
            timestamp = str(datetime.datetime.now())
            message['deviceid'] = self.sprinkler_id
            message['timestamp'] = timestamp
            message['datatype'] = 'Sprinkler_state'
            message['value'] = str(self.sprinkler_state_decide())
            messageJson = json.dumps(message)
            self.myAWSIoTMQTTClient.publish(self.topic, messageJson, 1)

            print("Published: '" + json.dumps(
                message) + "' to the topic: " + self.topic)
            break

if __name__ == '__main__':
    ###File location hardcoded in first three. After that, code will take any file inside a folder automatically.
    soil_sensor_1 = AWS("soil_sensor_1",
                        certificate="s1\\" + [file for file in os.listdir(
                            os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir) + '\\config\\s1')) if
                                              file.endswith("certificate.pem.crt")].pop(),
                        private_key="s1\\" + [file for file in os.listdir(
                            os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir) + '\\config\\s1')) if
                                              file.endswith("private.pem.key")].pop(),
                        root_path="s1\\" + [file for file in os.listdir(
                            os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir) + '\\config\\s1')) if
                                            file.endswith("CA1.pem")].pop(), sprinkler_state=False,
                        TOPIC="iot/agritech/s1", sprinkler_id='sp1')

    soil_sensor_2 = AWS("soil_sensor_2",
                        certificate="s2\\" + [file for file in os.listdir(
                            os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir) + '\\config\\s2')) if
                                              file.endswith("certificate.pem.crt")].pop(),
                        private_key="s2\\" + [file for file in os.listdir(
                            os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir) + '\\config\\s2')) if
                                              file.endswith("private.pem.key")].pop(),
                        root_path="s2\\" + [file for file in os.listdir(
                            os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir) + '\\config\\s2')) if
                                            file.endswith("CA1.pem")].pop(), sprinkler_state=False,
                        TOPIC="iot/agritech/s2", sprinkler_id='sp1')

    soil_sensor_3 = AWS("soil_sensor_3",
                        certificate="s3\\" + [file for file in os.listdir(
                            os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir) + '\\config\\s3')) if
                                              file.endswith("certificate.pem.crt")].pop(),
                        private_key="s3\\" + [file for file in os.listdir(
                            os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir) + '\\config\\s3')) if
                                              file.endswith("private.pem.key")].pop(),
                        root_path="s3\\" + [file for file in os.listdir(
                            os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir) + '\\config\\s3')) if
                                            file.endswith("CA1.pem")].pop(), sprinkler_state=False,
                        TOPIC="iot/agritech/s3", sprinkler_id='sp1')

    soil_sensor_4 = AWS("soil_sensor_4",
                        certificate="s4\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s4')) if
                                              file.endswith("certificate.pem.crt")].pop(),
                        private_key="s4\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s4')) if
                                              file.endswith("private.pem.key")].pop(),
                        root_path="s4\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s4')) if
                                            file.endswith("CA1.pem")].pop(), sprinkler_state=False,TOPIC="iot/agritech/s4",sprinkler_id='sp1')
    soil_sensor_5 = AWS("soil_sensor_5",
                        certificate="s5\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s5')) if
                                              file.endswith("certificate.pem.crt")].pop(),
                        private_key="s5\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s5')) if
                                              file.endswith("private.pem.key")].pop(),
                        root_path="s5\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s5')) if
                                            file.endswith("CA1.pem")].pop(), sprinkler_state=False,TOPIC="iot/agritech/s5",sprinkler_id='sp2')
    soil_sensor_6 = AWS("soil_sensor_6",
                        certificate="s6\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s6')) if
                                              file.endswith("certificate.pem.crt")].pop(),
                        private_key="s6\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s6')) if
                                              file.endswith("private.pem.key")].pop(),
                        root_path="s6\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s6')) if
                                            file.endswith("CA1.pem")].pop(), sprinkler_state=False,TOPIC="iot/agritech/s6",sprinkler_id='sp2')
    soil_sensor_7 = AWS("soil_sensor_7",
                        certificate="s7\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s7')) if
                                              file.endswith("certificate.pem.crt")].pop(),
                        private_key="s7\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s7')) if
                                              file.endswith("private.pem.key")].pop(),
                        root_path="s7\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s7')) if
                                            file.endswith("CA1.pem")].pop(), sprinkler_state=False,TOPIC="iot/agritech/s7",sprinkler_id='sp2')
    soil_sensor_8 = AWS("soil_sensor_8",
                        certificate="s8\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s8')) if
                                              file.endswith("certificate.pem.crt")].pop(),
                        private_key="s8\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s8')) if
                                              file.endswith("private.pem.key")].pop(),
                        root_path="s8\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s8')) if
                                            file.endswith("CA1.pem")].pop(), sprinkler_state=False,TOPIC="iot/agritech/s8",sprinkler_id='sp2')
    soil_sensor_9 = AWS("soil_sensor_9",
                        certificate="s9\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s9')) if
                                              file.endswith("certificate.pem.crt")].pop(),
                        private_key="s9\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s9')) if
                                              file.endswith("private.pem.key")].pop(),
                        root_path="s9\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s9')) if
                                            file.endswith("CA1.pem")].pop(), sprinkler_state=False,TOPIC="iot/agritech/s9",sprinkler_id='sp3')
    soil_sensor_10 = AWS("soil_sensor_10",
                        certificate="s10\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s10')) if
                                              file.endswith("certificate.pem.crt")].pop(),
                        private_key="s10\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s10')) if
                                              file.endswith("private.pem.key")].pop(),
                        root_path="s10\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s10')) if
                                            file.endswith("CA1.pem")].pop(), sprinkler_state=False,TOPIC="iot/agritech/s10",sprinkler_id='sp3')
    soil_sensor_11 = AWS("soil_sensor_11",
                        certificate="s11\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s11')) if
                                              file.endswith("certificate.pem.crt")].pop(),
                        private_key="s11\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s11')) if
                                              file.endswith("private.pem.key")].pop(),
                        root_path="s11\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s11')) if
                                            file.endswith("CA1.pem")].pop(), sprinkler_state=False,TOPIC="iot/agritech/s11",sprinkler_id='sp3')
    soil_sensor_12 = AWS("soil_sensor_12",
                        certificate="s12\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s12')) if
                                              file.endswith("certificate.pem.crt")].pop(),
                        private_key="s12\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s12')) if
                                              file.endswith("private.pem.key")].pop(),
                        root_path="s12\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s12')) if
                                            file.endswith("CA1.pem")].pop(), sprinkler_state=False,TOPIC="iot/agritech/s12",sprinkler_id='sp3')
    soil_sensor_13 = AWS("soil_sensor_13",
                        certificate="s13\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s13')) if
                                              file.endswith("certificate.pem.crt")].pop(),
                        private_key="s13\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s13')) if
                                              file.endswith("private.pem.key")].pop(),
                        root_path="s13\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s13')) if
                                            file.endswith("CA1.pem")].pop(), sprinkler_state=False,TOPIC="iot/agritech/s13",sprinkler_id='sp4')
    soil_sensor_14 = AWS("soil_sensor_14",
                        certificate="s14\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s14')) if
                                              file.endswith("certificate.pem.crt")].pop(),
                        private_key="s14\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s14')) if
                                              file.endswith("private.pem.key")].pop(),
                        root_path="s14\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s14')) if
                                            file.endswith("CA1.pem")].pop(), sprinkler_state=False,TOPIC="iot/agritech/s14",sprinkler_id='sp4')
    soil_sensor_15 = AWS("soil_sensor_15",
                        certificate="s15\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s15')) if
                                              file.endswith("certificate.pem.crt")].pop(),
                        private_key="s15\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s15')) if
                                              file.endswith("private.pem.key")].pop(),
                        root_path="s15\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s15')) if
                                            file.endswith("CA1.pem")].pop(), sprinkler_state=False,TOPIC="iot/agritech/s15",sprinkler_id='sp4')
    soil_sensor_16 = AWS("soil_sensor_16",
                        certificate="s16\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s16')) if
                                              file.endswith("certificate.pem.crt")].pop(),
                        private_key="s16\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s16')) if
                                              file.endswith("private.pem.key")].pop(),
                        root_path="s16\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s16')) if
                                            file.endswith("CA1.pem")].pop(), sprinkler_state=False,TOPIC="iot/agritech/s16",sprinkler_id='sp4')
    soil_sensor_17 = AWS("soil_sensor_17",
                        certificate="s17\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s17')) if
                                              file.endswith("certificate.pem.crt")].pop(),
                        private_key="s17\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s17')) if
                                              file.endswith("private.pem.key")].pop(),
                        root_path="s17\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s17')) if
                                            file.endswith("CA1.pem")].pop(), sprinkler_state=False,TOPIC="iot/agritech/s17",sprinkler_id='sp5')
    soil_sensor_18 = AWS("soil_sensor_18",
                        certificate="s18\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s18')) if
                                              file.endswith("certificate.pem.crt")].pop(),
                        private_key="s18\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s18')) if
                                              file.endswith("private.pem.key")].pop(),
                        root_path="s18\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s18')) if
                                            file.endswith("CA1.pem")].pop(), sprinkler_state=False,TOPIC="iot/agritech/s18",sprinkler_id='sp5')
    soil_sensor_19 = AWS("soil_sensor_19",
                        certificate="s19\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s19')) if
                                              file.endswith("certificate.pem.crt")].pop(),
                        private_key="s19\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s19')) if
                                              file.endswith("private.pem.key")].pop(),
                        root_path="s19\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s19')) if
                                            file.endswith("CA1.pem")].pop(), sprinkler_state=False,TOPIC="iot/agritech/s19",sprinkler_id='sp5')
    soil_sensor_20 = AWS("soil_sensor_20",
                        certificate="s20\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s20')) if
                                              file.endswith("certificate.pem.crt")].pop(),
                        private_key="s20\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s20')) if
                                              file.endswith("private.pem.key")].pop(),
                        root_path="s20\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\s20')) if
                                            file.endswith("CA1.pem")].pop(), sprinkler_state=False,TOPIC="iot/agritech/s20",sprinkler_id='sp5')
    sprinkler_1 = AWS_Sprinkler(
                        certificate="sp1\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\sp1')) if
                                              file.endswith("certificate.pem.crt")].pop(),
                        private_key="sp1\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\sp1')) if
                                              file.endswith("private.pem.key")].pop(),
                        root_path="sp1\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\sp1')) if
                                            file.endswith("CA1.pem")].pop(),TOPIC="iot/agritech/sprinkler/sprinkler1",sprinkler_id='sp1')
    sprinkler_2 = AWS_Sprinkler(
                        certificate="sp2\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\sp2')) if
                                              file.endswith("certificate.pem.crt")].pop(),
                        private_key="sp2\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\sp2')) if
                                              file.endswith("private.pem.key")].pop(),
                        root_path="sp2\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\sp2')) if
                                            file.endswith("CA1.pem")].pop(),TOPIC="iot/agritech/ssprinkler/sprinkler2",sprinkler_id='sp2')
    sprinkler_3 = AWS_Sprinkler(
                        certificate="sp3\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\sp3')) if
                                              file.endswith("certificate.pem.crt")].pop(),
                        private_key="sp3\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\sp3')) if
                                              file.endswith("private.pem.key")].pop(),
                        root_path="sp3\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\sp3')) if
                                            file.endswith("CA1.pem")].pop(),TOPIC="iot/agritech/ssprinkler/sprinkler3",sprinkler_id='sp3')
    sprinkler_4 = AWS_Sprinkler(
                        certificate="sp4\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\sp4')) if
                                              file.endswith("certificate.pem.crt")].pop(),
                        private_key="sp4\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\sp4')) if
                                              file.endswith("private.pem.key")].pop(),
                        root_path="sp4\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\sp4')) if
                                            file.endswith("CA1.pem")].pop(),TOPIC="iot/agritech/ssprinkler/sprinkler4",sprinkler_id='sp4')
    sprinkler_5 = AWS_Sprinkler(
                        certificate="sp5\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\sp5')) if
                                              file.endswith("certificate.pem.crt")].pop(),
                        private_key="sp5\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\sp5')) if
                                              file.endswith("private.pem.key")].pop(),
                        root_path="sp5\\" + [file for file in os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)+'\\config\\sp5')) if
                                            file.endswith("CA1.pem")].pop(),TOPIC="iot/agritech/ssprinkler/sprinkler5",sprinkler_id='sp5')

    sprinkler_1.publish()
    sprinkler_1.disconnect()
    # time.sleep(3)
    sprinkler_2.publish()
    sprinkler_2.disconnect()
    # time.sleep(3)
    sprinkler_3.publish()
    sprinkler_3.disconnect()
    sprinkler_4.publish()
    sprinkler_4.disconnect()
    sprinkler_5.publish()
    sprinkler_5.disconnect()
    soil_sensor_1.publish()
    soil_sensor_1.disconnect()
    # time.sleep(2)
    soil_sensor_2.publish()
    soil_sensor_2.disconnect()
    # time.sleep(2)
    soil_sensor_3.publish()
    soil_sensor_3.disconnect()
    # time.sleep(2)
    soil_sensor_4.publish()
    soil_sensor_4.disconnect()
    # time.sleep(2)
    soil_sensor_5.publish()
    soil_sensor_5.disconnect()
    soil_sensor_6.publish()
    soil_sensor_6.disconnect()
    soil_sensor_7.publish()
    soil_sensor_7.disconnect()
    soil_sensor_8.publish()
    soil_sensor_8.disconnect()
    soil_sensor_9.publish()
    soil_sensor_9.disconnect()
    soil_sensor_10.publish()
    soil_sensor_10.disconnect()
    soil_sensor_11.publish()
    soil_sensor_11.disconnect()
    soil_sensor_12.publish()
    soil_sensor_12.disconnect()
    soil_sensor_13.publish()
    soil_sensor_13.disconnect()
    soil_sensor_14.publish()
    soil_sensor_14.disconnect()
    soil_sensor_15.publish()
    soil_sensor_15.disconnect()
    soil_sensor_16.publish()
    soil_sensor_16.disconnect()
    soil_sensor_17.publish()
    soil_sensor_17.disconnect()
    soil_sensor_18.publish()
    soil_sensor_18.disconnect()
    soil_sensor_19.publish()
    soil_sensor_19.disconnect()
    soil_sensor_20.publish()
    soil_sensor_20.disconnect()
            # print(f'spr_list is {spr_list_with_obj}')
            # time.sleep(3)






