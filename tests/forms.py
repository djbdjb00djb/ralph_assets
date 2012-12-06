# -*- coding: utf-8 -*-

"""
This class testing assets forms
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from django.test import TestCase
from ralph.assets.models_assets import (
    Asset, AssetModel, AssetManufacturer, AssetSource, AssetStatus, AssetType,
    DeviceInfo, LicenseType, OfficeInfo, Warehouse
)
from ralph.ui.tests.helper import login_as_su

"""
Private methods
"""
def create_manufacturer(name):
    manufacturer = AssetManufacturer(name=name)
    manufacturer.save()
    return manufacturer


def create_model(manufacturer, name):
    model = AssetModel(
        manufacturer=manufacturer,
        name=name,
    )
    model.save()
    return model


def create_warehouse(name):
    warehouse = Warehouse(name=name)
    warehouse.save()
    return warehouse


def create_device(size, warehouse):
    device = DeviceInfo(
        size=size,
        warehouse=warehouse,
    )
    device.save()
    return device


def create_asset(**kwargs):
    asset = Asset(**kwargs)
    asset.save()
    return asset

"""
Testing classes
"""
class TestForms(TestCase):
    """
    This class testing adding, editing, deleting single asset
    """
    def setUp(self):
        # Hire we create django user and login him
        self.client = login_as_su()

        # We build output data
        asset = create_asset(
            device_info=create_device(1, create_warehouse(name='Warehouse1')),
            type=AssetType.data_center,
            model=create_model(create_manufacturer('Menufac'), 'AsModel'),
            source=AssetSource.shipment,
            invoice_no='Invoice No 1',
            order_no='Order No 1',
            invoice_date=datetime.datetime(2001, 01, 01),
            support_period=12,
            support_type='Support d2d',
            provider='Provider 1',
            status=AssetStatus.new,
            sn='sn-123',
            barcode='bc-1234'
        )

        # Now we add new manufacturer
        self.asset_model2 = create_model(
            create_manufacturer('Menufac2'), 'AsModel2'
        )

        # Device info
        self.device_info2 = create_device(
            1, create_warehouse(name='Warehouse2')
        )

        # And another one model
        self.asset_model3 = create_model(
            create_manufacturer('Menufac3'), 'AsModel3'
        )

    def test_models(self):
        """ Hire we testing setUp's """

        # There is Menufac in db
        db_manufacturer = AssetManufacturer.objects.get(name='Menufac')
        self.assertEquals(db_manufacturer.name, 'Menufac')

        # There is AsModel in db
        db_model = AssetModel.objects.get(name='AsModel')
        self.assertEquals(db_model.name, 'AsModel')

        # There is  Warehouse1 in db
        db_warehouse = Warehouse.objects.get(name='Warehouse1')
        self.assertEquals(db_warehouse.name, 'Warehouse1')

        # There is asset in db
        db_asset1 = Asset.objects.get(barcode='bc-1234')
        self.assertEquals(db_asset1.sn, 'sn-123')

    def test_view(self):
        """ Here we testing whether correct data is displayed in table"""

        # Request GET
        url = '/assets/dc/search'
        view = self.client.get(url, follow=True)
        self.assertEqual(view.status_code, 200)

        # Geting first row to test
        data = view.context_data['page'].object_list[0]

        # Type field
        self.assertEqual(data.type, AssetType.data_center)

        # SN field
        self.assertEqual(data.sn, 'sn-123')

        # Barcode field
        self.assertEqual(data.barcode, 'bc-1234')

        # Model field
        self.assertEqual(unicode(data.model), 'Menufac AsModel')

        # Invoice no field
        self.assertEqual(data.invoice_no, 'Invoice No 1')

        # Order no field
        self.assertEqual(data.order_no, 'Order No 1')

        # Invoice date field
        date = datetime.date(2001, 1, 1)
        self.assertEqual(data.invoice_date, date)

        # Status field
        self.assertEqual(data.status, AssetStatus.new)

        # Warehouse field
        self.assertEqual(unicode(data.device_info.warehouse), 'Warehouse1')

    def test_add_form(self):
        """
        Everything is ok? Now we trying add new data via form.
        So let's dance!
        """
        # Hire we prepare some data and send it via form
        url = '/assets/dc/add/device/'
        post_data = {
            'type': AssetType.data_center,
            'model': self.asset_model2.id,
            'source': AssetSource.shipment,
            'invoice_no': 'Invoice No 2',
            'order_no': 'Order No 2',
            'invoice_date': '2001-01-02',
            'support_period': 12,
            'support_type': 'Support d2d',
            'support_void_reporting': 'on',
            'provider': 'Provider 2',
            'status': AssetStatus.new,
            'size': 1,
            'sn': 'sn-321',
            'barcode': 'bc-4321',
            'warehouse': self.device_info2.warehouse_id,
        }
        response = self.client.post(url, post_data, follow=True)

        # When everything was ok, server return response code = 302, and
        # redirect as to /assets/dc/search given response code 200
        self.assertRedirects(
            response, '/assets/dc/search',
            status_code=302,
            target_status_code=200,
        )

        # So see what was added (of course in secound table row)
        view = self.client.get('/assets/dc/search')
        data = view.context_data['page'].object_list[1]

        # Type field
        self.assertEqual(data.type, AssetType.data_center)

        # SN field
        self.assertEqual(data.sn, 'sn-321')

        # Barcode field
        self.assertEqual(data.barcode, 'bc-4321')

        # Model field
        self.assertEqual(unicode(data.model), 'Menufac2 AsModel2')

        # Invoice no field
        self.assertEqual(data.invoice_no, 'Invoice No 2')

        # Order no field
        self.assertEqual(data.order_no, 'Order No 2')

        # Invoice data field
        date = datetime.date(2001, 1, 2)
        self.assertEqual(data.invoice_date, date)

        # Status field
        self.assertEqual(data.status, AssetStatus.new)

        # Warehosue field
        self.assertEqual(unicode(data.device_info.warehouse), 'Warehouse2')

    def test_edit_form(self):
        # Done, Add data via form was correct!  Now change some informations

        # Download old data
        view = self.client.get('/assets/dc/edit/device/1/')
        self.assertEqual(view.status_code, 200)
        old_fields = view.context['asset_form'].initial
        old_device_info = view.context['device_info_form'].initial
        old_office_info = view.context['office_info_form'].initial

        # Now we checking what licese_key is None
        old_office = OfficeInfo.objects.filter(
            license_key='0000-0000-0000-0000'
        ).count()
        self.assertEqual(old_office, 0)

        # Next way is send new data via form
        url = '/assets/dc/edit/device/1/'
        post_data = {
            'type': AssetType.data_center,
            'model': self.asset_model3.id,
            'invoice_no': 'Invoice No 3',
            'order_no': 'Order No 3',
            'invoice_date': '2001-02-02',
            'support_period': 24,
            'support_type': 'standard',
            'support_void_reporting': 'on',
            'provider': 'Provider 3',
            'status': AssetStatus.in_progress,
            'size': 2,
            'sn': 'sn-321-2012',
            'barcode': 'bc-4321-2012',
            'warehouse': self.device_info2.warehouse_id,
            'remarks': 'any remarks',
            'size': 2,
            'license_key': '0000-0000-0000-0000',
            'version': '1.0',
            'unit_price': 2.00,
            'license_type': LicenseType.oem,
            'invoice_date': '2001-02-02',
            'date_of_last_inventory': '2003-02-02',
            'last_logged_user': 'James Bond',
        }
        post = self.client.post(url, post_data, follow=True)

        # and checking whether data was added
        self.assertRedirects(
            post,
            '/assets/dc/search',
            status_code=302,
            target_status_code=200,
        )

        # So now we downloading added data
        new_view = self.client.get('/assets/dc/edit/device/1/')
        new_fields = new_view.context['asset_form'].initial
        new_device_info = new_view.context['device_info_form'].initial
        new_office_info = new_view.context['office_info_form'].initial

        # prepare correct data
        correct_data = [
            dict(
                model=self.asset_model3.id,
                invoice_no='Invoice No 3',
                order_no='Order No 3',
                invoice_date='2001-02-02',
                support_period=24,
                support_type='standard',
                provider='Provider 3',
                status=AssetStatus.in_progress.id,
                remarks='any remarks'
            )
        ]

        # and testing (new data is deferent old data, and new data is equal to
        # correct data). Hire we testing: model, invoice_no, order_no,
        # invoice_date, support_period, support_type, provider, status, remarks
        for data in correct_data:
            for key in data.keys():
                self.assertNotEqual(
                    unicode(old_fields[key]), unicode(new_fields[key])
                )
                self.assertEqual(
                    unicode(new_fields[key]), unicode(data[key])
                )

        # Size field
        self.assertNotEqual(old_device_info['size'], new_device_info['size'])
        self.assertEqual(new_device_info['size'], 2)

        # License field (download from db, new <> old data
        office = OfficeInfo.objects.filter(
            license_key='0000-0000-0000-0000'
        ).count()
        self.assertEqual(office, 1)
        self.assertEqual(old_office_info, {})
        self.assertEqual(new_office_info['license_key'], '0000-0000-0000-0000')

        # Prepare ackoffice's fields
        correct_data_office = [
            dict(
                version='1.0',
                unit_price=2,
                license_type=LicenseType.oem.id,
                date_of_last_inventory='2003-02-02',
                last_logged_user='James Bond',
            )
        ]

        # And testing: version, unit_price, license_type,
        # date_of_last_inventory, last_logged_user
        for office in correct_data_office:
            for key in office.keys():
                self.assertEqual(
                    unicode(new_office_info[key]), unicode(office[key])
                )

    def test_delete_asset(self):
        # FIXME!
        pass


class TestBulkEdit(TestCase):
    """
    This class testing forms for may actions
    """
    def setUp(self):
        # cerate and login django user
        self.client = login_as_su()

        # Build asset
        self.asset = create_asset(
            device_info=create_device(1, create_warehouse(name='Warehouse1')),
            type=AssetType.data_center,
            model=create_model(create_manufacturer('Menufac1'), 'AsModel1'),
            source=AssetSource.shipment,
            invoice_no='Invoice No 1',
            order_no='Order No 1',
            invoice_date=datetime.datetime(2001, 01, 01),
            support_period=12,
            support_type='Support d2d',
            provider='Provider 1',
            status=AssetStatus.new,
            sn='sn-123',
            barcode='bc-1234'
        )
        # Build secound asset
        self.asset2 = create_asset(
            device_info=create_device(1, create_warehouse(name='Warehouse2')),
            type=AssetType.data_center,
            model=create_model(create_manufacturer('Menufac2'), 'AsModel2'),
            source=AssetSource.shipment,
            invoice_no='Invoice No 2',
            order_no='Order No 2',
            invoice_date=datetime.datetime(2002, 01, 01),
            support_period=22,
            support_type='Support d2d',
            provider='Provider 2',
            status=AssetStatus.new,
            sn='sn-1232',
            barcode='bc-12342'
        )

    def test_bulkedit_form(self):
        """
         This class testing Bulk edit form
        """

        # Download base data
        url = '/assets/dc/bulkedit/?select=%s&select=%s' % (
            self.asset.id, self.asset2.id)
        view = self.client.get(url)
        self.assertEqual(view.status_code, 200)

        # Prepare new data
        model0 = create_model(create_manufacturer('Menufac1a'), 'AsModel1a')
        model1 = create_model(create_manufacturer('Menufac2a'), 'AsModel2a')
        post_data = {
            'form-TOTAL_FORMS': u'2',
            'form-INITIAL_FORMS': u'2',
            'form-MAX_NUM_FORMS': u'',
            'form-0-id': 1,
            'form-0-type': AssetType.data_center.id,
            'form-0-model': model0.id,
            'form-0-invoice_no': 'Invoice No 1a',
            'form-0-order_no': 'Order No 1a',
            'form-0-invoice_date': '2012-02-02',
            'form-0-sn': 'sn-321-2012a',
            'form-0-barcode': 'bc-4321-2012a',
            'form-0-support_period': 24,
            'form-0-support_type': 'standard1',
            'form-0-support_void_reporting': 'on',
            'form-0-provider': 'Provider 1a',
            'form-0-status': AssetStatus.in_progress.id,
            'form-0-source': AssetSource.shipment.id,
            'form-1-id': 2,
            'form-1-type': AssetType.data_center.id,
            'form-1-model': model1.id,
            'form-1-invoice_no': 'Invoice No 2a',
            'form-1-order_no': 'Order No 2a',
            'form-1-invoice_date': '2011-02-03',
            'form-1-sn': 'sn-321-2012b',
            'form-1-barcode': 'bc-4321-2012b',
            'form-1-support_period': 48,
            'form-1-support_type': 'standard2',
            'form-1-support_void_reporting': 'off',
            'form-1-provider': 'Provider 2a',
            'form-1-status': AssetStatus.waiting_for_release.id,
            'form-1-source': AssetSource.shipment.id,
        }
        post = self.client.post(url, post_data, follow=True)

        # When everything was ok, server return response code = 302, and
        # redirect as to /assets/dc/search given response code 200
        self.assertRedirects(
            post, url, status_code=302, target_status_code=200,
        )

        # Download new data
        new_view = self.client.get(url)
        fields = new_view.context['formset'].queryset

        # and prepare correct data
        correct_data = [
            dict(
                model=unicode(model0),
                invoice_no='Invoice No 1a',
                order_no='Order No 1a',
                invoice_date='2012-02-02',
                support_period=24,
                support_type='standard1',
                provider='Provider 1a',
                status=AssetStatus.in_progress.id,
                sn='sn-321-2012a',
                barcode='bc-4321-2012a'
            ),
            dict(
                model=unicode(model1),
                invoice_no='Invoice No 2a',
                order_no='Order No 2a',
                invoice_date='2011-02-03',
                support_period=48,
                support_type='standard2',
                provider='Provider 2a',
                status=AssetStatus.waiting_for_release.id,
                sn='sn-321-2012b',
                barcode='bc-4321-2012b'
            )
        ]

        # Testing fields in all rows: model, invoice_no, order_no, invoice_date
        # support_period, support_type, provider, status, sn, barcode
        counter = 0
        for data in correct_data:
            for key in data.keys():
                self.assertEqual(
                    unicode(getattr(fields[counter], key)), unicode(data[key])
                )
            counter = counter + 1


class TestSearchForm(TestCase):
    """
    This class testing search form
    """
    def setUp(self):
        # new user and loging
        self.client = login_as_su()

        # Prepare new asset
        model = create_model(create_manufacturer('Menufac1'), 'AsModel1')
        self.asset = create_asset(
            device_info=create_device(1, create_warehouse(name='Warehouse1')),
            type=AssetType.data_center,
            model=model,
            source=AssetSource.shipment,
            invoice_no='Invoice No 1',
            order_no='Order No 1',
            invoice_date=datetime.datetime(2001, 01, 01),
            support_period=12,
            support_type='Support d2d',
            provider='Provider 1',
            status=AssetStatus.new,
            sn='sn-12332452345',
            barcode='bc-123421141'
        )

        # Secound one
        self.asset1 = create_asset(
            device_info=create_device(1, create_warehouse(name='Warehouse2')),
            type=AssetType.data_center,
            model=create_model(create_manufacturer('Menufac2'), 'AsModel2'),
            source=AssetSource.shipment,
            invoice_no='Invoice No 1',
            order_no='Order No 3',
            invoice_date=datetime.datetime(2003, 01, 01),
            support_period=12,
            support_type='Support d2d',
            provider='Provider 2',
            status=AssetStatus.in_service,
            sn='sn-123123123',
            barcode='bc-1234123123'
        )
        # Third one
        self.asset2 = create_asset(
            device_info=create_device(1, create_warehouse(name='Warehouse3')),
            type=AssetType.data_center,
            model=model,
            source=AssetSource.shipment,
            invoice_no='Invoice No 3',
            order_no='Order No 3',
            invoice_date=datetime.datetime(2002, 01, 01),
            support_period=12,
            support_type='standard',
            provider='Provider 3',
            status=AssetStatus.used,
            sn='sn-12323542345',
            barcode='bc-12341234124'
        )

    def test_model(self):
        # Hire is testing model field

        # Is there any asset?
        url = '/assets/dc/search?model=%s' % self.asset.id
        get = self.client.get(url)
        self.assertEqual(get.status_code, 200)

        # yes, there are 2 assets (first and therd)
        res = get.context_data['page'].object_list
        self.assertEqual(len(res), 2)

        # and is on list second asset?
        output = ('<Asset: AsModel2 - sn-123123123 - bc-1234123123>')
        self.assertNotEqual(unicode(res[0]), output)

        # now we go wronging!
        # What do Ralph when we don't insert model id? (return all asset)
        url = '/assets/dc/search?model='
        get = self.client.get(url)
        self.assertEqual(get.status_code, 200)
        res = get.context_data['page'].object_list
        self.assertEqual(len(res), 3)

        # or we insert wrond id (after range)?
        url = '/assets/dc/search?model=99999'
        get = self.client.get(url)
        self.assertEqual(get.status_code, 404)

    def test_invoice(self):
        # Hire is testing invoice field

        # There is any asset in Invoice No 1?
        url = '/assets/dc/search?invoice_no=%s' % 'Invoice No 1'
        get = self.client.get(url)
        self.assertEqual(get.status_code, 200)

        # How many Ralph return results?
        res = get.context_data['page'].object_list
        self.assertEqual(len(res), 2)

        # Is there third asset in list?
        output = ('<Asset: AsModel3 - sn-12323542345 - bc-12341234124>')
        self.assertNotEqual(unicode(res[0]), output)

    def test_order(self):
        # Hire is testing order no field

        # There is any asset in Order No 3?
        url = '/assets/dc/search?order_no=%s' % 'Order No 3'
        get = self.client.get(url)
        self.assertEqual(get.status_code, 200)

        # How many Ralph returns results?
        res = get.context_data['page'].object_list
        self.assertEqual(len(res), 2)

        # Is there first asset in list?
        output = ('<Asset: AsModel1 - sn-12332452345 - bc-123421141>')
        self.assertNotEqual(unicode(res[0]), output)

    def test_provider(self):
        # Hire is testing provider field
        url = '/assets/dc/search?provider=%s' % 'Provider 3'
        get = self.client.get(url)
        self.assertEqual(get.status_code, 200)

        # How many results Ralph return?
        res = get.context_data['page'].object_list
        self.assertEqual(len(res), 1)

        # Is there first asset?
        output = ('<Asset: AsModel1 - sn-12332452345 - bc-123421141>')
        self.assertNotEqual(unicode(res[0]), output)

    def test_status(self):
        # Hire is testing status field
        url = '/assets/dc/search?status=%s' % AssetStatus.used.id
        get = self.client.get(url)
        self.assertEqual(get.status_code, 200)

        # How many results Ralph return?
        res = get.context_data['page'].object_list
        self.assertEqual(len(res), 1)

        # Is there first asset?
        output = ('Menufac1 AsModel1 - sn-12323542345 - bc-12341234124')
        self.assertEqual(unicode(res[0]), output)

    def test_sn(self):
        # Hire is testing sn field
        url = '/assets/dc/search?sn=%s' % 'sn-123123123'
        get = self.client.get(url)
        self.assertEqual(get.status_code, 200)

        # How many results Ralph return?
        res = get.context_data['page'].object_list
        self.assertEqual(len(res), 1)

        # Is there secound asset?
        output = ('Menufac2 AsModel2 - sn-123123123 - bc-1234123123')
        self.assertEqual(unicode(res[0]), output)

    def test_date_range(self):
        # Hire is testing data range of invoice field
        # beggining date should be equal than end date
        url = '/assets/dc/search?invoice_date_from=%s&invoice_date_to=%s' % (
            '2001-01-01', '2001-01-01')
        get = self.client.get(url)
        self.assertEqual(get.status_code, 200)
        res = get.context_data['page'].object_list
        self.assertEqual(len(res), 1)
        output = ('Menufac1 AsModel1 - sn-12332452345 - bc-123421141')
        self.assertEqual(unicode(res[0]), output)
        # beggining date should be lower than end date
        url = '/assets/dc/search?invoice_date_from=%s&invoice_date_to=%s' % (
            '2001-01-01', '2002-01-01')
        get = self.client.get(url)
        self.assertEqual(get.status_code, 200)
        res = get.context_data['page'].object_list
        self.assertEqual(len(res), 2)
        output = ('AsModel2 - sn-123123123 - bc-1234123123')
        self.assertNotEqual(unicode(res[0]), output)
        # beggining date can't be lower than end date
        url = '/assets/dc/search?invoice_date_from=%s&invoice_date_to=%s' % (
            '2011-01-01', '2002-01-01')
        get = self.client.get(url)
        self.assertEqual(get.status_code, 200)
        res = get.context_data['page'].object_list
        self.assertEqual(len(res), 0)
        # beggining date is None, end date is desirable
        url = '/assets/dc/search?invoice_date_from=%s&invoice_date_to=%s' % (
            '', '2001-01-01')
        get = self.client.get(url)
        self.assertEqual(get.status_code, 200)
        res = get.context_data['page'].object_list
        self.assertEqual(len(res), 1)
        # beggining date is None, end date is lower then youngest object
        url = '/assets/dc/search?invoice_date_from=%s&invoice_date_to=%s' % (
            '', '1999-01-01')
        get = self.client.get(url)
        self.assertEqual(get.status_code, 200)
        res = get.context_data['page'].object_list
        self.assertEqual(len(res), 0)
        # beggining date is correct, end date is None
        url = '/assets/dc/search?invoice_date_from=%s&invoice_date_to=%s' % (
            '1999-01-01', '')
        get = self.client.get(url)
        self.assertEqual(get.status_code, 200)
        res = get.context_data['page'].object_list
        self.assertEqual(len(res), 3)


class TestTrolling(TestCase):
    """
    This class testing forms validation
    """
    def setUp(self):
        # create and loging django user
        self.client = login_as_su()

        # Prepare required fields (formset_name, field_name)
        self.required_fields = [
            ('asset_form', 'model'),
            ('asset_form', 'support_period'),
            ('asset_form', 'support_type'),
            ('device_info_form', 'warehouse'),
            ('asset_form', 'sn')
        ]

        # Build first asset
        self.asset = create_asset(
            device_info=create_device(1, create_warehouse(name='Warehouse1')),
            type=AssetType.data_center,
            model=create_model(create_manufacturer('Menufac1'), 'AsModel1'),
            source=AssetSource.shipment,
            invoice_no='Invoice No 1',
            order_no='Order No 1',
            invoice_date=datetime.datetime(2001, 01, 01),
            support_period=12,
            support_type='Support d2d',
            provider='Provider 1',
            status=AssetStatus.new,
            sn='sn-123',
            barcode='bc-1234'
        )
        # Build secound asset
        self.asset2 = create_asset(
            device_info=create_device(1, create_warehouse(name='Warehouse2')),
            type=AssetType.data_center,
            model=create_model(create_manufacturer('Menufac2'), 'AsModel2'),
            source=AssetSource.shipment,
            invoice_no='Invoice No 2',
            order_no='Order No 2',
            invoice_date=datetime.datetime(2002, 01, 01),
            support_period=22,
            support_type='Support d2d',
            provider='Provider 2',
            status=AssetStatus.new,
            sn='sn-1232',
            barcode='bc-12342'
        )

    def test_empty_add_form(self):
        # try send empty form
        url = '/assets/back_office/add/device/'
        post_data = {}
        post = self.client.post(url, post_data)
        self.assertEqual(post.status_code, 200)

        # seeing that all required fields returns error: model, support_period,
        # support_type, warehouse, sn
        for r in self.required_fields:
            self.assertFormError(
                post, r[0], r[1], 'This field is required.'
            )

    def test_empty_edit_form(self):
        # try send empty form
        url = '/assets/dc/edit/device/1/'
        post_data = {}
        post = self.client.post(url, post_data)
        self.assertEqual(post.status_code, 200)

        # seeing that all required fields returns error: model, support_period,
        # support_type, warehouse, sn
        for r in self.required_fields:
            self.assertFormError(
                post, r[0], r[1], 'This field is required.'
            )

    def test_bulkedit2_form(self):
        # testing bulk edit form with wrong data

        # prepare wrong data to send via bulk edit form
        url = '/assets/dc/bulkedit/?select=%s&select=%s' % (
            self.asset.id, self.asset2.id)
        model0 = create_model(create_manufacturer('Menufac1a'), 'AsModel1a')
        model1 = create_model(create_manufacturer('Menufac2a'), 'AsModel2a')
        post_data = {
            'form-TOTAL_FORMS': u'2',
            'form-INITIAL_FORMS': u'2',
            'form-MAX_NUM_FORMS': u'',
            'form-0-id': 1,
            'form-0-type': AssetType.data_center.id,
            'form-0-model': model0.id,
            'form-0-invoice_no': 'Invoice No 1a',
            'form-0-order_no': 'Order No 1a',
            'form-0-invoice_date': 'wrong_field_data',
            'form-0-sn': 'sn-1232',
            'form-0-barcode': 'bc-4321-2012a',
            'form-0-support_period': 24,
            'form-0-support_type': 'standard1',
            'form-0-support_void_reporting': 'on',
            'form-0-provider': 'Provider 1a',
            'form-0-status': AssetStatus.in_progress.id,
            'form-0-source': AssetSource.shipment.id,
            'form-1-id': 2,
            'form-1-type': AssetType.data_center.id,
            'form-1-model': '',
            'form-1-invoice_no': 'Invoice No 2a',
            'form-1-order_no': 'Order No 2a',
            'form-1-invoice_date': '2011-02-03',
            'form-1-sn': 'sn-321-2012a',
            'form-1-barcode': 'bc-4321-2012b',
            'form-1-support_period': 48,
            'form-1-support_type': 'standard2',
            'form-1-support_void_reporting': 'off',
            'form-1-provider': 'Provider 2a',
            'form-1-status': '',
            'form-1-source': '',
        }
        post = self.client.post(url, post_data)

        # check whether post was send (correct = False)
        try:
            self.assertRedirects(
                post, url, status_code=302, target_status_code=200,
            )
            send_post = True
        except AssertionError:
            send_post = False
        self.assertEqual(send_post, False)

        # Prepare fields error
        bulk_data = [
            dict(
                row=0,
                field='invoice_date',
                error='Enter a valid date.',
            ),
            dict(
                row=0,
                field='sn',
                error='Asset with this Sn already exists.',
            ),
            dict(
                row=1,
                field='model',
                error='This field is required.',
            ),
            dict(
                row=1,
                field='source',
                error='This field is required.',
            ),
            dict(
                row=1,
                field='status',
                error='This field is required.',
            )
        ]

        # and testing
        for bulk in bulk_data:
            formset = post.context_data['formset']
            self.assertEqual(
                formset[bulk['row']]._errors[bulk['field']][0],
                bulk['error']
            )

        # if sn was duplicated application send message, so seeing whether
        # error message was displayed
        find = []
        i = 0
        msg_error = 'Please correct duplicated serial numbers or barcodes.'
        for i in range(len(post.content)):
            if post.content.startswith(msg_error, i - 1):
                find.append(i)
        self.assertTrue(len(find) == 1)

        # Next prepare correct data
        post_data = {
            'form-TOTAL_FORMS': u'2',
            'form-INITIAL_FORMS': u'2',
            'form-MAX_NUM_FORMS': u'',
            'form-0-id': 1,
            'form-0-type': AssetType.data_center.id,
            'form-0-model': model0.id,
            'form-0-invoice_no': 'Invoice No 1a',
            'form-0-order_no': 'Order No 1a',
            'form-0-invoice_date': '2012-02-01',
            'form-0-sn': 'sn-1232aad',
            'form-0-barcode': 'bc-4321-2012a',
            'form-0-support_period': 24,
            'form-0-support_type': 'standard1',
            'form-0-support_void_reporting': 'on',
            'form-0-provider': 'Provider 1a',
            'form-0-status': AssetStatus.in_progress.id,
            'form-0-source': AssetSource.shipment.id,
            'form-1-id': 2,
            'form-1-type': AssetType.data_center.id,
            'form-1-model': model1.id,
            'form-1-invoice_no': 'Invoice No 2a',
            'form-1-order_no': 'Order No 2a',
            'form-1-invoice_date': '2011-02-03',
            'form-1-sn': 'sn-321-2012a',
            'form-1-barcode': 'bc-4321-2012b',
            'form-1-support_period': 48,
            'form-1-support_type': 'standard2',
            'form-1-support_void_reporting': 'off',
            'form-1-provider': 'Provider 2a',
            'form-1-status': AssetStatus.waiting_for_release.id,
            'form-1-source': AssetSource.shipment.id,
        }
        correct_post = self.client.post(url, post_data, follow=True)
        # See wither all is ok
        self.assertRedirects(
            correct_post, url, status_code=302, target_status_code=200,
        )
        # And find success message
        find = []
        i = 0
        msg_error = 'Changes saved.'
        for i in range(len(correct_post.content)):
            if correct_post.content.startswith(msg_error, i - 1):
                find.append(i)
        self.assertEqual(len(find), 1)

    def test_invalid_fueld_value(self):
        # instead of integers we send strings, error should be thrown
        url = '/assets/back_office/add/device/'
        post_data = {
            'support_period': 'string',
            'size': 'string',
            'invoice_date': 'string'
        }
        post = self.client.post(url, post_data)
        self.assertEqual(post.status_code, 200)

        # other fields error
        self.assertFormError(
            post, 'asset_form', 'support_period', 'Enter a whole number.'
        )
        self.assertFormError(
            post, 'device_info_form', 'size', 'Enter a whole number.'
        )
        self.assertFormError(
            post, 'asset_form', 'invoice_date', 'Enter a valid date.'
        )
