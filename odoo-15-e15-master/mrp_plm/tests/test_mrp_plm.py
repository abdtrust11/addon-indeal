# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from .test_common import TestPlmCommon


class TestMrpPlm(TestPlmCommon):

    def test_rebase_with_old_bom_change(self):
        "Test eco rebase with old bom changes."

        # Create eco for bill of material.
        self.eco1 = self._create_eco('ECO1', self.bom_table, self.eco_type.id, self.eco_stage.id)
        # Start new revision of eco1.
        self.eco1.action_new_revision()

        # Eco should be in progress and new revision of BoM should be created.
        self.assertTrue(self.eco1.new_bom_id, "New revision of bill of material should be created.")
        self.assertEqual(self.eco1.state, 'progress', "Wrong state on eco")

        # Change old bom lines
        old_bom_leg = self.bom_table.bom_line_ids.filtered(lambda x: x.product_id == self.table_leg)
        new_bom_leg = self.eco1.new_bom_id.bom_line_ids.filtered(lambda x: x.product_id == self.table_leg)

        # Update quantity current bill of materials.
        old_bom_leg.product_qty = 8

        # Check status of eco
        self.assertEqual(self.eco1.state, 'rebase', "Wrong state on eco.")
        self.assertEqual(new_bom_leg.product_qty, 3, "Wrong table leg quantity on new revision of BoM.")

        # Rebase eco1 with current BoM changes ( 3 + 5 ( New added product )).
        self.eco1.apply_rebase()

        # Check quantity of table lag on new revision of BoM.
        self.assertEqual(new_bom_leg.product_qty, 8, "Wrong table leg quantity on new revision of bom.")

        # Add new bom line with product bolt in old BoM.
        self.env['mrp.bom.line'].create({'product_id': self.table_bolt.id, 'bom_id': self.bom_table.id, 'product_qty': 3})

        # Check status of eco and rebase line after adding new product on current BoM.
        self.assertEqual(self.eco1.state, 'rebase', "Wrong state on eco.")
        self.assertEqual(len(self.eco1.bom_rebase_ids), 1, "Wrong rebase line on eco.")
        self.assertEqual(self.eco1.bom_rebase_ids.change_type, 'add', "Wrong type on rebase line.")

        # Rebase eco1 with BoM changes.
        self.eco1.apply_rebase()

        new_bom_bolt = self.eco1.new_bom_id.bom_line_ids.filtered(lambda x: x.product_id == self.table_bolt)

        # Check eco status and bom line should be added on new bom revision.
        self.assertTrue(new_bom_bolt, "BoM line should be added for bolt on new revision of BoM.")
        self.assertEqual(self.eco1.state, 'progress', "Wrong state on eco.")

        # Remove line form current BoM
        self.eco1.bom_id.bom_line_ids.filtered(lambda x: x.product_id == self.table_bolt).unlink()

        # Check status of eco with rebase lines.
        self.assertEqual(self.eco1.state, 'rebase', "Wrong state on eco.")
        self.assertEqual(len(self.eco1.bom_rebase_ids), 1, "Wrong BoM rebase line on eco.")
        self.assertEqual(self.eco1.bom_rebase_ids.change_type, 'update', "Wrong type on rebase line.")
        self.assertEqual(self.eco1.bom_rebase_ids.upd_product_qty, -3, "Wrong quantity on rebase line.")

        # Rebase eco
        self.eco1.apply_rebase()
        self.assertFalse(self.eco1.new_bom_id.bom_line_ids.filtered(lambda x: x.product_id == self.table_bolt), "BoM line should be unlink from new revision of BoM.")

        # Change old BoM leg and new revision BoM leg quantity.
        old_bom_leg.product_qty = 10
        new_bom_leg.product_qty = 12
        self.assertEqual(self.eco1.bom_rebase_ids.change_type, 'update', "Wrong type on rebase line.")
        self.assertEqual(self.eco1.bom_rebase_ids.upd_product_qty, 2, "Wrong quantity on rebase line.")

        # Rebase ecos with changes of old bill of material.
        self.eco1.apply_rebase()
        self.assertEqual(self.eco1.state, 'conflict', "Wrong state on eco.")

        # Manually resolve conflict.
        self.eco1.conflict_resolve()
        self.assertEqual(self.eco1.state, 'progress', "Wrong state on eco.")

    def test_rebase_with_previous_eco_change(self):
        "Test eco rebase with previous eco changes."

        # --------------------------------
        # Create ecos for bill of material.
        # ---------------------------------

        eco1 = self._create_eco('ECO1', self.bom_table, self.eco_type.id, self.eco_stage.id)
        eco2 = self._create_eco('ECO2', self.bom_table, self.eco_type.id, self.eco_stage.id)
        eco3 = self._create_eco('ECO3', self.bom_table, self.eco_type.id, self.eco_stage.id)

        # Start new revision of eco1, eco2, eco3
        eco1.action_new_revision()
        eco2.action_new_revision()
        eco3.action_new_revision()

        # -----------------------------------------
        # Check eco status after start new revision.
        # ------------------------------------------

        self.assertEqual(eco1.state, 'progress', "Wrong state on eco1.")
        self.assertEqual(eco2.state, 'progress', "Wrong state on eco2.")
        self.assertEqual(eco3.state, 'progress', "Wrong state on eco2.")

        # ---------------------------------------------------------------
        # ECO 1 : Update Table Leg quantity in new BoM revision.
        # ---------------------------------------------------------------

        eco1_new_table_leg = eco1.new_bom_id.bom_line_ids.filtered(lambda x: x.product_id == self.table_leg)
        eco1_new_table_leg.product_qty = 6

        # -------------------------------------------------------------------------------
        # ECO 1 : Check status of ecos after apply changes and activate new bom revision.
        # -------------------------------------------------------------------------------

        eco1.action_apply()
        self.assertFalse(eco1.bom_id.active, "Old BoM of eco1 should be deactivated.")
        self.assertTrue(eco1.new_bom_id.active, "New BoM revision of ECO 1 should be activated.")
        # Check eco status after activate new bom revision of eco.
        self.assertEqual(eco1.state, 'done', "Wrong state on eco1.")
        self.assertEqual(eco2.state, 'rebase', "Wrong state on eco2.")
        self.assertEqual(eco3.state, 'rebase', "Wrong state on eco3.")

        # ------------------------------
        # ECO 2 : Rebase with ECO 1 changes.
        # ------------------------------

        eco2.apply_rebase()
        self.assertEqual(eco2.state, 'progress', "Wrong state on eco2.")
        self.assertEqual(eco1.new_bom_id.id, eco2.bom_id.id, "Eco2 BoM should replace with new activated BoM revision of Eco1.")

        # ----------------------------------------------------------------------
        # ECO 2 : Add new product 'Table Bolt'
        # ----------------------------------------------------------------------

        eco2.new_bom_id.bom_line_ids.create({'product_id': self.table_bolt.id, 'bom_id': eco2.new_bom_id.id, 'product_qty': 3})
        self.assertTrue(eco2.bom_change_ids, "Eco 2 should have BoM change lines.")

        # -------------------------------------------------------------------------------
        # ECO 2 : Check status of after apply changes and activate new bom revision.
        # -------------------------------------------------------------------------------

        eco2.action_apply()

        self.assertFalse(eco1.bom_id.active, "BoM of ECO 1 should be deactivated")
        self.assertFalse(eco1.new_bom_id.active, "BoM revision of ECO 1 should be deactivated")
        self.assertTrue(eco2.new_bom_id.active, "BoM revision of ECO 2 should be activated")

        # -----------------------------------------------------
        # ECO3 : Change same line in eco3 as changes in eco1.
        # ----------------------------------------------------

        eco3_new_table_leg = eco3.new_bom_id.bom_line_ids.filtered(lambda x: x.product_id == self.table_leg)
        eco3_new_table_leg.product_qty = 4

        # -----------------------------------
        # Rebase eco3 with eco1 BoM changes.
        # -----------------------------------

        eco3.apply_rebase()

        # Check status of eco3 after rebase.
        self.assertEqual(eco3.state, 'conflict', "Wrong state on eco.")

        # Resolve conflict manually.
        self.assertTrue(eco3.previous_change_ids.ids, "Wrong previous bom change on bom lines.")
        eco3.conflict_resolve()
        self.assertEqual(eco3.state, 'progress', "Wrong state on eco.")
        eco3.action_apply()
        self.assertFalse(eco2.new_bom_id.active, "BoM revision of ECO 2 should be deactivated")
        self.assertTrue(eco3.new_bom_id.active, "BoM revision of ECO 3 should be activated")
        self.assertFalse(eco3.previous_change_ids.ids)
        self.assertFalse(eco3.bom_rebase_ids.ids)

    def test_operation_change(self):
        "Test eco with bom operation changes."
        # --------------------------------
        # Create ecos for bill of material.
        # ---------------------------------

        eco1 = self._create_eco('ECO1', self.bom_table, self.eco_type.id, self.eco_stage.id)

        # Start new revision of eco1
        eco1.action_new_revision()

        # -----------------------------------------
        # Check eco status after start new revision.
        # ------------------------------------------

        self.assertEqual(eco1.state, 'progress', "Wrong state on eco1.")

        # ---------------------------------------------------------------
        # ECO 1 : Update duration on operation1
        # ---------------------------------------------------------------

        op1 = eco1.new_bom_id.operation_ids.filtered(lambda x: x.workcenter_id == self.workcenter_1)
        op1.time_cycle_manual = 20

        # ---------------------------------------------------------------
        # ECO 1 : Remove operation2
        # ---------------------------------------------------------------

        op2 = eco1.new_bom_id.operation_ids.filtered(lambda x: x.workcenter_id == self.workcenter_2)
        op2.unlink()

        # ---------------------------------------------------------------
        # ECO 1 : Add operation3
        # ---------------------------------------------------------------

        eco1.new_bom_id.operation_ids.create({
            'name': 'op3',
            'bom_id': eco1.new_bom_id.id,
            'workcenter_id': self.workcenter_3.id,
            'time_cycle_manual': 10,
            'sequence': 2,
        })

        # Check correctness
        op1_change = eco1.routing_change_ids.filtered(lambda x: x.workcenter_id == self.workcenter_1)
        self.assertEqual(op1_change.change_type, 'update', "Wrong type on opration change line.")
        self.assertEqual(op1_change.upd_time_cycle_manual, 10.0, "Wrong duration change.")

        op2_change = eco1.routing_change_ids.filtered(lambda x: x.workcenter_id == self.workcenter_2)
        self.assertEqual(op2_change.change_type, 'remove', "Wrong type on opration change line.")

        op3_change = eco1.routing_change_ids.filtered(lambda x: x.workcenter_id == self.workcenter_3)
        self.assertEqual(op3_change.change_type, 'add', "Wrong type on opration change line.")
        self.assertEqual(op1_change.upd_time_cycle_manual, 10.0, "Wrong duration change.")
