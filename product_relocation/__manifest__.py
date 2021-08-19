# -*- coding: utf-8 -*-

###################################################################################
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

{
    'name': 'Product relocation',
    'version': '0.0.1',
    'summary': 'Product relocation',
    'author': 'gflores',
    'maintainer': 'gflores',
    'company': 'Grupo Requiez SA de CV',
    'website': 'https://www.gruporequiez.com',
    'depends': ['stock'],
    'category': 'Inventory',
    'demo': [],
    'data': [
        # security
        'security/product_location_security.xml',
        "security/ir.model.access.csv",
        # views
        'wizard/product_relocation_wizard.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
