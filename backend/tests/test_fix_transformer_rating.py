"""Unit tests for transformer rating extraction logic."""
from unittest.mock import MagicMock
from src.shared.cim_model import CimModelManager

def test_transformer_kva_extraction_logic():
    """Verify that CimModelManager correctly identifies transformer ratings."""
    manager = CimModelManager()
    manager.cim = MagicMock()
    manager.network = MagicMock()
    
    # Mock CIM classes
    manager.cim.ConnectivityNode = "CN"
    manager.cim.Terminal = "Terminal"
    manager.cim.PowerTransformer = "PT"
    manager.cim.PowerTransformerEnd = "PTE"
    manager.cim.TransformerTank = "Tank"
    manager.cim.TransformerTankInfo = "TankInfo"
    manager.cim.TransformerEndInfo = "EndInfo"
    
    # Mock objects in graph
    # PowerTransformer with PTE
    pt1 = MagicMock(mRID="_pt1")
    pte1 = MagicMock(mRID="_pte1", ratedS=75000.0, endNumber=1)
    pte1.PowerTransformer = pt1
    
    # TransformerTank with TankInfo (no ends)
    tank1 = MagicMock(mRID="_tank1")
    t_info1 = MagicMock(mRID="_ti1")
    te_info1 = MagicMock(mRID="_ei1", ratedS=25000.0)
    te_info1.TransformerTankInfo = t_info1
    tank1.AssetDatasheet = t_info1
    
    manager.network.graph = {
        manager.cim.PowerTransformer: {"_pt1": pt1},
        manager.cim.PowerTransformerEnd: {"_pte1": pte1},
        manager.cim.TransformerTank: {"_tank1": tank1},
        manager.cim.TransformerTankInfo: {"_ti1": t_info1},
        manager.cim.TransformerEndInfo: {"_ei1": te_info1},
    }
    
    # Run the logic
    manager._build_transformer_index()
    
    # Verify PT1 rating from PTE1
    assert manager._transformer_kva["PT1"] == 75.0
    
    # Verify Tank1 rating from TankInfo fallback (since no TankEnds exist)
    assert manager._transformer_kva["TANK1"] == 25.0
    
def test_mrid_normalization():
    from src.shared.cim_model import _mrid_str
    class Obj:
        def __init__(self, m): self.mRID = m
        
    assert _mrid_str(Obj("urn:uuid:123")) == "123"
    assert _mrid_str(Obj("_ABC")) == "ABC"
    assert _mrid_str(Obj("xyz")) == "XYZ"
