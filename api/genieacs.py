# -*- coding: utf-8 -*-
#
# python-genieacs
# A Python API to interact with the GenieACS REST API
# https://github.com/TDT-GmbH/python-genieacs

import requests
import json

class Connection(object):
    """Connection object to interact with the GenieACS server."""
    def __init__(self, ip, port=7557, ssl=False, verify=False, auth=False, user="", passwd="", url="", timeout=10):
        self.server_ip = ip
        self.server_port = port
        self.use_ssl = ssl
        self.ssl_verify = verify
        self.use_auth = auth
        self.username = user
        self.password = passwd
        self.server_url = url
        self.timeout = timeout
        self.base_url = ""
        self.session = None
        self.__set_base_url()
        self.__create_session()

    def __set_base_url(self):
        if not self.use_ssl:
            self.base_url = "http://"
        else:
            self.base_url = "https://"
        self.base_url += self.server_ip + ":" + str(self.server_port) + self.server_url

    def __create_session(self):
        if self.session is None:
            self.session = requests.Session()
            if self.use_auth:
                self.session.auth = (self.username, self.password)
            if self.use_ssl:
                self.session.verify = self.ssl_verify
        try:
            # do a request to test the connection
            self.file_get_all()
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError):
            raise ConnectionError

    def __request_get(self, url):
        request_url = self.base_url + url
        try:
            r = self.session.get(request_url, timeout=self.timeout)
            r.raise_for_status()
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError):
            raise ConnectionError
        if r.text:
            data = r.json()
            return data

    def __request_post(self, url, data, conn_request=True):
        if conn_request:
            request_url = self.base_url + url + "?connection_request"
        else:
            request_url = self.base_url + url
        try:
            r = self.session.post(request_url, json=data, timeout=self.timeout)
            r.raise_for_status()
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError):
            raise ConnectionError
        if r.text:
            data = r.json()
            return data

    def __request_put(self, url, data, headers=None):
        request_url = self.base_url + url
        try:
            if headers is not None:
                r = self.session.put(request_url, data, timeout=self.timeout, headers=headers)
            else:
                r = self.session.put(request_url, data, timeout=self.timeout)
            r.raise_for_status()
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError):
            raise ConnectionError
        if r.text:
            data = r.json()
            return data

    def __request_delete(self, url):
        request_url = self.base_url + url
        try:
            r = self.session.delete(request_url, timeout=self.timeout)
            r.raise_for_status()
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError):
            raise ConnectionError
        if r.text:
            data = r.json()
            return data

    ##### methods for devices #####

    def device_get_all_IDs(self):
        """Get IDs of all devices"""
        jsondata = self.__request_get("/devices/" + "?projection=_id")
        data = []
        for device in jsondata:
            data.append(device["_id"])
        return data

    def device_get_by_id(self, device_id):
        """Get all data of a device identified by its ID"""
        quoted_id = requests.utils.quote("{\"_id\":\"" + device_id + "\"}", safe = '')
        return self.__request_get("/devices/" + "?query=" + quoted_id)

    def device_get_by_MAC(self, device_MAC):
        """Get all data of a device identified by its MAC address"""
        quoted_MAC = requests.utils.quote("{\"summary.mac\":\"" + device_MAC + "\"}", safe = '')
        return self.__request_get("/devices/" + "?query=" + quoted_MAC)

    def device_get_by_serial(self, device_serial):
        """Get all data of a device identified by its Serial"""
        quoted_serial = requests.utils.quote("{\"InternetGatewayDevice.DeviceInfo.SerialNumber\":\"" + device_serial + "\"}", safe = '')
        return self.__request_get("/devices/" + "?query=" + quoted_serial)

    def device_get_parameter(self, device_id, parameter_name):
        """Directly get the value of a given parameter from a given device"""
        quoted_id = requests.utils.quote("{\"_id\":\"" + device_id + "\"}", safe = '')
        data = self.__request_get("/devices" + "?query=" + quoted_id + "&projection=" + parameter_name)
        try:
            value = data[0]
            if parameter_name in ["_tags", "_lastInform", "_registered", "_lastBootstrap", "_lastBoot", "_deviceId"]:
                for part in parameter_name.split('.'):
                    value = value[part]
                return value
            else:
                for part in parameter_name.split('.'):
                    value = value[part]
                return value["_value"]
        except (IndexError, KeyError):
            return None

    def device_get_parameters(self, device_id, parameter_names):
        """Get a defined list of parameters from a given device"""
        quoted_id = requests.utils.quote("{\"_id\":\"" + device_id + "\"}", safe = '')
        data = self.__request_get("/devices" + "?query=" + quoted_id + "&projection=" + parameter_names)
        try:
            data = data[0]
            values = {}
            src = data
            dest = values
        except (IndexError):
            return {}
        for parameter in parameter_names.split(','):
            parameter_parts = parameter.split('.')
            for part in parameter_parts:
                if part != parameter_parts[-1]:
                    try:
                        src = src[part]
                    except (KeyError):
                        src[part] = {}
                        src = src[part]
                    if part not in dest.keys():
                        dest[part] = {}
                    dest = dest[part]
                else:
                    try:
                        dest[part] = src[part]["_value"]
                    except (KeyError):
                        dest[part] = None
                    dest = values
                    src = data
        return values

    def device_delete(self, device_id):
        """Delete a given device from the database"""
        self.__request_delete("/devices/" + requests.utils.quote(device_id))

    ##### methods for tasks #####

    def task_get_all(self, device_id=None):
        if device_id:
            """Get all existing tasks of a given device"""
            quoted_id = requests.utils.quote("{\"device\":\"" + device_id + "\"}", safe = '')
            return self.__request_get("/tasks/" + "?query=" + quoted_id)
        else:
            """Get all existing tasks"""
            return self.__request_get("/tasks/")

    def task_refresh_object(self, device_id, object_name, conn_request=True):
        """Create a refreshObject task for a given device"""
        data = { "name": "refreshObject",
                 "objectName": object_name }
        try:
            return self.__request_post("/devices/" + requests.utils.quote(device_id) + "/tasks", data, conn_request)
        except requests.exceptions.HTTPError:
            raise ItemNotFoundError

    def task_set_parameter_values(self, device_id, parameter_values, conn_request=True):
        """Create a setParameterValues task for a given device"""
        data = { "name": "setParameterValues",
                 "parameterValues": parameter_values }
        try:
            return self.__request_post("/devices/" + requests.utils.quote(device_id) + "/tasks", data, conn_request)
        except requests.exceptions.HTTPError:
            raise ItemNotFoundError

    def task_get_parameter_values(self, device_id, parameter_names, conn_request = True):
        """Create a getParameterValues task for a given device"""
        data = { "name": "getParameterValues",
                "parameterNames": parameter_names}
        try:
            return self.__request_post("/devices/" + requests.utils.quote(device_id) + "/tasks", data, conn_request)
        except requests.exceptions.HTTPError:
            raise ItemNotFoundError

    def task_add_object(self, device_id, object_name, object_path, conn_request=True):
        """Create an addObject task for a given device"""
        data = { "name": "addObject", object_name : object_path}
        try:
            return self.__request_post("/devices/" + requests.utils.quote(device_id) + "/tasks", data, conn_request)
        except requests.exceptions.HTTPError:
            raise ItemNotFoundError

    def task_reboot(self, device_id, conn_request=True):
        """Create a reboot task for a given device"""
        data = { "name": "reboot"}
        try:
            return self.__request_post("/devices/" + requests.utils.quote(device_id) + "/tasks", data, conn_request)
        except requests.exceptions.HTTPError:
            raise ItemNotFoundError

    def task_factory_reset(self, device_id, conn_request=True):
        """Create a factoryReset task for a given device"""
        data = { "name": "factoryReset"}
        try:
            return self.__request_post("/devices/" + requests.utils.quote(device_id) + "/tasks", data, conn_request)
        except requests.exceptions.HTTPError:
            raise ItemNotFoundError

    def task_download(self, device_id, file_id, filename, conn_request=True):
        """Create a download task for a given device"""
        data = { "name": "download", "file": file_id, "filename": filename}
        try:
            return self.__request_post("/devices/" + requests.utils.quote(device_id) + "/tasks", data, conn_request)
        except requests.exceptions.HTTPError:
            raise ItemNotFoundError

    def task_retry(self, task_id):
        "Retry a faulty task at the next inform"
        try:
            return self.__request_post("/tasks/" + task_id + "/retry", None)
        except requests.exceptions.HTTPError:
            raise ItemNotFoundError

    def task_delete(self, task_id):
        """Delete a Task for a given device"""
        try:
            return self.__request_delete("/tasks/" + task_id)
        except requests.exceptions.HTTPError:
            raise ItemNotFoundError

    ##### methods for tags ######

    def tag_get_all(self, device_id):
        """Get all existing tags of a given device"""
        quoted_id = requests.utils.quote("{\"_id\":\"" + device_id + "\"}", safe = '')
        data = self.__request_get("/devices" + "?query=" + quoted_id + "&projection=_tags")
        try:
            return data[0]["_tags"]
        except (IndexError, KeyError):
            return []

    def tag_assign(self, device_id, tag_name):
        """Assign a tag to a device"""
        try:
            self.__request_post("/devices/" + requests.utils.quote(device_id) + "/tags/" + tag_name, None, False)
        except requests.exceptions.HTTPError:
            raise ItemNotFoundError

    def tag_remove(self, device_id, tag_name):
        """Remove a tag from a device"""
        try:
            self.__request_delete("/devices/" + requests.utils.quote(device_id) + "/tags/" + tag_name)
        except requests.exceptions.HTTPError:
            raise ItemNotFoundError

    ##### methods for presets #####

    def preset_get_all(self, filename=None):
        """Get all existing presets as a json object, optionally write them to a file"""
        data = self.__request_get("/presets")
        try:
            if filename is not None:
                f = open(filename, 'w')
                json.dump(data, f, indent=4, separators=(',', ': '))
                f.close()
        except IOError as err:
            print("preset_get_all:\nIOError: " + str(err) + "\n")
        finally:
            return data

    def preset_create(self, preset_name, data):
        """Create a new preset or update a preset with a given name"""
        quoted_name = requests.utils.quote(preset_name)
        try:
            self.__request_put("/presets/" + quoted_name, data)
        except requests.exceptions.HTTPError:
            raise InvalidRequestDataError

    def preset_create_all_from_file(self, filename):
        """Create all presets contained in a json file"""
        try:
            f = open(filename, 'r')
            data = json.load(f)
            f.close()
            for preset in data:
                preset_name = requests.utils.quote(preset["_id"])
                del preset["_id"]
                self.__request_put("/presets/" + preset_name, json.dumps(preset))
        except IOError as err:
            print("preset_create_all_from_file:\nIOError: " + str(err) + "\n")
        except ValueError:
            print("preset_create_all_from_file:\nValueError: File contains faulty values\n")
        except KeyError:
            print("preset_create_all_from_file:\nKeyError: File contains faulty keys\n")

    def preset_delete(self, preset_name):
        """Delete a given preset"""
        quoted_name = requests.utils.quote(preset_name)
        try:
            self.__request_delete("/presets/" + quoted_name)
        except requests.exceptions.HTTPError:
            raise ItemNotFoundError

    ##### methods for objects #####

    def object_get_all(self, filename=None):
        """Get all existing objects as a json object, optionally write them to a file"""
        data = self.__request_get("/objects")
        try:
            if filename is not None:
                f = open(filename, 'w')
                json.dump(data, f, indent=4, separators=(',', ': '))
                f.close()
        except IOError as err:
            print("object_get_all:\nIOError: " + str(err) + "\n")
        finally:
            return data

    def object_create(self, object_name, data):
        """Create a new object or update an object with a given name"""
        quoted_name = requests.utils.quote(object_name)
        try:
            self.__request_put("/objects/" + quoted_name, data)
        except requests.exceptions.HTTPError:
            raise InvalidRequestDataError

    def object_create_all_from_file(self, filename):
        """Create all objects contained in a json file"""
        try:
            f = open(filename, 'r')
            data = json.load(f)
            f.close()
            for gobject in data:
                object_name = requests.utils.quote(gobject["_id"])
                del gobject["_id"]
                self.__request_put("/objects/" + object_name, json.dumps(gobject))
        except IOError as err:
            print("object_create_all_from_file:\nIOError: " + str(err) + "\n")
        except ValueError:
            print("object_create_all_from_file:\nValueError: File contains faulty values\n")
        except KeyError:
            print("object_create_all_from_file:\nKeyError: File contains faulty keys\n")

    def object_delete(self, object_name):
        """Delete a given object"""
        quoted_name = requests.utils.quote(object_name)
        try:
            self.__request_delete("/objects/" + quoted_name)
        except requests.exceptions.HTTPError:
            raise ItemNotFoundError

    ##### methods for provisions #####

    def provision_get_all(self, filename=None):
        """Get all existing provisions as a json object, optionally write them to a file"""
        data = self.__request_get("/provisions")
        try:
            if filename is not None:
                f = open(filename, 'w')
                json.dump(data, f, indent=4, separators=(',', ': '))
                f.close()
        except IOError as err:
            print("provision_get_all:\nIOError: " + str(err) + "\n")
        finally:
            return data

    def provision_create(self, provision_name, data):
        """Create a new provision or update a provision with a given name"""
        quoted_name = requests.utils.quote(provision_name)
        try:
            self.__request_put("/provisions/" + quoted_name, data)
        except requests.exceptions.HTTPError:
            raise InvalidRequestDataError

    def provision_create_all_from_file(self, filename):
        """Create all provisions contained in a json file"""
        try:
            f = open(filename, 'r')
            data = json.load(f)
            f.close()
            for provision in data:
                provision_name = requests.utils.quote(provision["_id"])
                provision_data = provision["script"]
                self.__request_put("/provisions/" + provision_name, provision_data)
        except IOError as err:
            print("provision_create_all_from_file:\nIOError: " + str(err) + "\n")
        except ValueError:
            print("provision_create_all_from_file:\nValueError: File contains faulty values\n")
        except KeyError:
            print("provision_create_all_from_file:\nKeyError: File contains faulty keys\n")

    def provision_delete(self, provision_name):
        """Delete a given provision"""
        quoted_name = requests.utils.quote(provision_name)
        try:
            self.__request_delete("/provisions/" + quoted_name)
        except requests.exceptions.HTTPError:
            raise ItemNotFoundError

    ##### methods for files #####

    def file_upload(self, filename, fileType, oui, productClass, version):
        """Upload or update a file"""
        try:
            self.__request_put("/files/" + filename, data=open(filename, "rb"), headers={"fileType": fileType, "oui": oui, "productClass": productClass, "version" : version})
        except IOError as err:
            print("file_upload:\nIOError: " + str(err) + "\n")

    def file_delete(self, filename):
        """Delete a given file"""
        self.__request_delete("/files/" + filename)

    def file_get_all(self):
        """Get all files as a json object"""
        return self.__request_get("/files")

    def file_get(self, filename=None, fileType=None, oui=None, productClass=None, version=None):
        """Get all data from one or several files"""
        url = "{"
        if filename is not None:
            url += "\"filename\":\"" + filename + "\""
        else:
            if fileType is not None:
                if url != "{":
                    url += ","
                url += "\"metadata.fileType\":\"" + fileType + "\""
            if oui is not None:
                if url != "{":
                    url += ","
                url += "\"metadata.oui\":\"" + oui + "\""
            if productClass is not None:
                if url != "{":
                    url += ","
                url += "\"metadata.productClass\":\"" + productClass + "\""
            if version is not None:
                if url != "{":
                    url += ","
                url += "\"metadata.version\":\"" + version + "\""
        if url == "{":
            raise InvalidRequestDataError
        return self.__request_get("/files/?query=" + requests.utils.quote(url + "}", safe = ''))

    ##### methods for faults #####

    def fault_get_all_IDs(self):
        """Get IDs of all faults"""
        jsondata = self.__request_get("/faults/" + "?projection=_id")
        data = []
        for fault in jsondata:
            data.append(fault["_id"])
        return data

    def fault_get_all(self, device_id=None):
        if device_id:
            """Get all existing faults for a given device"""
            quoted_id = requests.utils.quote("{\"device\":\"" + device_id + "\"}", safe = '')
            return self.__request_get("/faults/" + "?query=" + quoted_id)
        else:
            """Get all existing faults"""
            return self.__request_get("/faults/")

    def fault_delete(self, fault_id):
        """Delete a given fault"""
        quoted_id = requests.utils.quote(fault_id)
        try:
            self.__request_delete("/faults/" + quoted_id)
        except requests.exceptions.HTTPError:
            raise ItemNotFoundError

class ConnectionError(Exception):
    def __str__(self):
        return "Could not (re-)connect to the ACS"

class ItemNotFoundError(Exception):
    def __str__(self):
        return "Could not find the requested item (device, task, preset, object, file, etc)"

class InvalidRequestDataError(Exception):
    def __str__(self):
        return "Request contained invalid data"