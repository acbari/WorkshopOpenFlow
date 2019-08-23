1. Copy all files into vm modul-workshop
2. Run mininet

   sudo mn --switch=ovs,protocols=OpenFlow13 --controller=remote
3. Run controller

   ryu-manager monitor_controller.py
4. Run mointor apps
   - python flowmon record_name observation_size
   
     example: python flowmon.py sw1-1-9a:36:8c:99:90:d7 50
   - python portmon.py record_ame observation_size
   
     example: python portmon.py sw1-1 50
