 🎉ployment!n deproductiody for ow reaackend is nop bectShePerfr Th``

Youloyment
`rce-new-depfo-service --fectshopice theperervcluster --sfectshop-theperster e --clu-servicupdatecs y
aws e Deplolatest

#op-backend:eperfectshnaws.com/theast-1.amazodkr.ecr.us-t>.ush <accoun
docker pd:latesttshop-backenperfeccom/thezonaws..amat-1ecr.us-eas>.dkr.ntatest <accouckend:lbactshop-g theperfer tad .
docke-backenerfectshop-t thepr build 
dockews.comonaeast-1.amazecr.us-kr.unt>.dstdin <acco-password- AWS -rnamesein --uker log| doc1 st-us-eagion sword --regin-pascr get-lo push
aws e
# Build and`bashS:**
``## **AWS EC
#
```
8000/health/localhost:rl http:/
cu -dompose upocker-cle .env
dv.examp
cp .enndackesh
cd b:**
```baal Docker **Loc
###mmands
tart Co 🎯 Quick S
---

##et up
eline sCI/CD pip- [ ] mplemented
p strategy i] Backugured
- [ gging confilotoring and ] Moniing
- [ tion worknd integra ] Fronteted
- [ts tesoinendp
- [ ] API ent:**st-Deploym
### **Pod
figurete conL certifica ] SScer
- [anload balnting to  name poiDomain[ ] assing
- lth checks p[ ] Heaigured
- confd balancer  ] Loaunning
- [e rand servicS cluster le
- [ ] EC accessibcreated andse  databa ] RDSushed
- [uilt and pmage b[ ] Docker ited
- ository creaECR rep**
- [ ] Deployment:WS 
### **A
ng no errorsogs showi[ ] L run
- grationsase mi
- [ ] Databhealth`)00/localhost:80://`curl httpresponding ( ] API  [`)
-pose pser-comhy (`docks healtll service
- [ ] Alsuccessfuose up -d` er-comp `dock [ ]ent:**
-ploymocker De

### **Don)cti produed (forconfigurme  naain [ ] Domtion)
-ucr prod (foeadyes rificatert [ ] SSL cecured
-tials scredentabase 
- [ ] Daiguredonfiables cnt varnme ] Enviro- [nd running
alled acker inst*
- [ ] Doployment:*Pre-De

### **tcklisnt Che 📋 Deployme
##

---
``xxxxx
`xx-ids sg-xxoup --grurity-groupsribe-sec descups
aws ec2ty groCheck securi
# tshop-db
rfec thepeentifierce-idb-instances --dnstanbe-db-i descriues
aws rdsssnnection ise coaba Dat
#n>
ask-arsks <t--taop-cluster ectshr theperfstecluibe-tasks --descrng
aws ecs tiart st task no`bash
# ECSes:**
``ssun AWS I
### **Commo
```
rune -aem pdocker systpace
disk s
# Out of ain
and login ag
# Logout USERcker $rmod -aG do
sudo useedission deni
# Perminer_id>
onta stop <cps
dockerdocker 
n useready iPort al
# 
```bash*ssues:*ocker I# **Common Dooting

## 🆘 Troublesh##--



-t
```-deploymen-force-newvice -erhop-sfectstheperservice --ster ctshop-cluer theperfelust--cte-service ecs upda       aws  |
   un:     rECS
   to loy : Dep    - nameTAG

  IMAGE_:$EPOSITORYCR_R/$E_REGISTRY $ECRer pushock     d  AG .
   GE_TY:$IMAREPOSITORCR_EGISTRY/$EECR_Ruild -t $    docker b     un: |
        r}
 ithub.sha }AG: ${{ gIMAGE_T         -backend
 tshoperfecORY: thep_REPOSIT     ECR
     gistry }}uts.retpcr.oun-e{ steps.logiREGISTRY: ${      ECR_nv:
           eon ECR
 mage to Amazand push iild, tag,   - name: Bu
    in@v1
on-ecr-logns/amaz: aws-actio uses
       ogin-ecr      id: l
  azon ECRto Am Login  - name:
     -east-1
: usaws-region
          S_KEY }}_ACCESWS_SECRETrets.Aec{ scess-key: ${ret-acws-sec      a
    SS_KEY_ID }}S_ACCE{ secrets.AW: ${cess-key-id    aws-ac
          with:ls@v2
    redentia-aws-configurews-actions/cs: a     uses
   ntiale AWS credefigurme: Con     - na   
 3
   heckout@vctions/c uses: a   - steps:
   test
   tu-las-on: ubun
    runy:  deplos:

job [main]
hes:branch:
    pus

on:
  ploy to AWSame: Deyaml
nl`:
```loy.ymeps/db/workflowithu
Create `.gCI/CD**
b Actions **GitHu

### ionAutomatt oymen Depl
---

## 🚀30/month)
ss (~$rleRDS Serve + daambrless**: L3. **Serve/month)
icro (~$503.mate + RDS t**: ECS FargProductionl . **Smalth)
2/mon (~$25p RunnerApment**: lop
1. **Deve Options:**t-Effective **Cos
###ics
custom metrdWatch: 10 ours
- Clou 750 h Balancer:ation Loadplicours
- Ap ho for 750: db.t2.micrRDSh
- urs per monte: 20GB-ho Fargat
- ECSurces:**e Tier Reso**AWS Freon

###  Optimizati💰 Cost

## ---ly

 properRS- Enable COimiting
t rate llemen- Imps
 JWT secretse strongS/SSL
- Unable HTTPy**
- E Securittion*Applica## *

#ransit in tat rest andencryption s
- Enable ired accesequh minimal r groups wittyuriase
- Secor databe subnets f private VPC with
- Usy** Securittwork

### **Nes keys accesnstead of irolesM  Use IAs to Git
-cretommit seever c- Ntive data
sifor senManager S Secrets  Use AW
-Variables**Environment 
### **ices
Best Practrity  Secu
## 🔒

---
`: `/metricstoringstom Monieady`
- Cu `/health/r Check: Healthth`
- ALBhealheck: `/Health CS - ECecks**
ealth Ch# **H
```

##--followerfectshop l /ecs/thepais tgs
aws log# View lo

hoprfects/ecs/thepeoup-name --log-gre-log-group ats creaws logp
log grouh
# Create asLogs**
```bloudWatch 
### **C & Logging
Monitoring-

## 📊 
--t-1
```
N=us-easREGIO# AWS
AWS_

ain.comrdom://www.youin.com,httpsurdomas://yohttpS_ORIGINS=
# CORS
COR
oduction=prNMENT
ENVIRO
DEBUG=false32-charskey-tion-ecure-produc-ssuperY=SECRET_KErity
Secu79/0

# point:63che-endsticala://your-e_URL=redisEDIStshop
Rerfec2/thepaws.com:543azonoint.amrds-endpour-rd@yasswo:pshoptheperfect://esql=postgrE_URLS)
DATABAS (RD Database
#```bash
v)**duction (.en# **Pro

##0
```lhost:808,http://loca3000st:localho=http://S_ORIGINSRS
CORent

# COT=developmENVIRONMENrue
UG=tg
DEBaracters-lonchkey-32-ecret-ev-sCRET_KEY=drity
SE
# Secu
host:6379/0s://localL=redi_URtshop
REDISfec2/theper:5433@localhostshop12heperfecttshop:techeperfesql://tgrE_URL=postse
DATABASatabah
# D**
```bas (.env)opmentel
### **Devn
nfiguratiovironment Co

## 🔧 En
```

---guidedploy --uild
sam debash
sam b

```: ANY
```      Method+}
      proxyath: /{           Pties:
     Proper    : Api
  ype        T  teway:
     ApiGaEvents:
   11
      3.time: pythonun  Rer
    r.handla_handledler: lambd   Han  eUri: .
      Codties:
 
    Properion::Functerverlesse: AWS::SPI:
    TypectShopA:
  ThePerf
Resources0-31
016-1erverless-2AWS::Sransform: 
T2010-09-09': 'ormatVersionmplateF
AWSTeml.yaemplate```yaml
# tM:**
h AWS SAity w
3. **Deplo
```
pp)angum(aler = Mapp

handort pp.main impum
from aangport M mangum imn
frompythor.py:**
```handleambda_. **Create l

2ngum
``` install ma`bash
pipSGI:**
``r All Mangum foInsta**

1. rverless)**da (SeWS Lambtion C: A## **Op
```

#}'GB"
  "0.5 ": emory
    "M5 vCPU",Cpu": "0.2 '{
    "gurationstance-confi--in \
  rue
  }'abled": ttsEnploymen"AutoDe},
    CR"
    ype": "EyTpositor  "ImageRe,
    "
      } "8000rt":        "Potion": {
nfigura "ImageCot",
     ckend:latesectshop-batheperfonaws.com/az-1.amstcr.us-ea.dkr.e<account-id>r": "geIdentifie  "Ima   tory": {
 geReposi "Iman '{
   iguratioource-conf--s  ckend \
fectshop-bapere thee-nam  --servicervice \
create-sr nneaws apprush
**
```baRunner:App oy with  **Depl
2."
```
ret-key-sece: "yourlu   va  _KEY
 e: SECRET- nam
    l"se-uryour-databa "e:    valu
  ASE_URLATABe: D:
    - nam PORT
  env0
    env:rt: 800   ponetwork:
   8000
port 0.0.0.0 --t in:app --hosicorn app.mad: uv11
  commann: 3.ime-versiorunt
  run:ments.txt
re requill -r- pip instaild:
      :
    buommands
build:
  cython3time: prunion: 1.0
rs
```yaml
ve*er.yaml:*te apprunn

1. **Creaest)**r (SimplApp RunneS : AW# **Option B
```

##ENABLED}"ignPublicIp=,assxxxxxxxx]=[sg-xrityGroupsxxxx],secuxxxet-xxs=[subnion={subnetratwsvpcConfiguion "ak-configurat
  --networ\E pe FARGATunch-ty\
  --laed-count 1 ir--des\
  -backend:1 oprfectsh thepeoninitideftask- --ervice \
 shop-se theperfect-nam  --servicecluster \
ectshop-rfster thepe\
  --clu eate-servicecs crrvice
aws eate se

# Crejson-definition.file://task-json i-inputition --clr-task-defingiste reecson
aws  definitier taskstgi`bash
# Re:
``uner and r

Regist
  ]
}
``` }  }
         }
    
  ecs"efix": "m-progs-streawsl "a       -1",
  ast"us-e": regionlogs-   "aws",
       opctshfethepers/: "/ec-group"logs       "aws{
   ptions":  "o  ",
     slogsawr": "gDrive      "lo
  ration": {iguonfogC    "l    ],
  
    }rs"
      te-characcret-key-32-secure-se"your-superue":     "val      _KEY",
RET: "SEC"name       "   {
        ,
       }tion"
 ": "produc"value      ENT",
    RONMme": "ENVI "na
           {     },
    op"
     tsheperfec:5432/thds-endpointur-r@yohop:passwordtheperfectssql://stgre: "poue"  "val
        SE_URL",BA": "DATA      "name
     {  [
     nment": viro   "en ],
   
         }   : "tcp"
 ol"   "protoc     : 8000,
  ort"erP"contain       {
   
        pings": [apportM  "    
est",-backend:laterfectshopcom/thepaws.st-1.amazonr.us-ea.dkr.ecnt-id>ccou": "<a"image ",
     ndshop-backefectperame": "the"n      [
    {
": ionserDefinitain  "cont
ole",nRtioecsTaskExecuid>:role/::<account-:aws:iamrnleArn": "a"executionRo",
  ": "512memory6",
  ": "25"cpu"  ARGATE"],
ies": ["Fmpatibilit"requiresCopc",
  sv"awMode": networkd",
  "ackenshop-brfecthepemily": "t"fan
{
  ``jsojson`:
`nition.sk-defi
Create `taervice**
ploy ECS S: DeStep 2## **E
```

##FARGATroviders -pcapacityuster ---clopshe theperfecter-nam--clust-cluster s ecs createh
aw`bas**
``ster:CS Clu*Create E`

4. *ncrypted
``rage-e--sto
  riod 7 \-peionntup-rete\
  --backme default oup-na-grubnet  --db-s \
xxxg-xxxxxxoup-ids surity-grec\
  --vpc-srage 20 ocated-sto--all
  ssword123 \rSecurePard You-user-passwoter \
  --maseperfectshop-username th --master\
 stgres e po\
  --engin.micro lass db.t3e-c-db-instanc  -p-db \
eperfectshoifier thance-ident-inst --dbe \
 nce-db-instacreath
aws rds basbase:**
```S Datareate RD3. **C

est
```backend:laterfectshop-m/thep.co.amazonawsus-east-1.ecr.krunt-id>.dpush <accoer mage
docksh iPust

# :lateckendp-baeperfectsho/thzonaws.comma.ar.us-east-1kr.ecnt-id>.dcoutest <acd:lackenbactshop-perfethedocker tag age
 Tag imckend .

#tshop-baheperfecild -t tbu
docker d imageBuil
# s.com
zonawst-1.amaear.us-r.ecd>.dknt-iaccoud-stdin <WS --passwor Arname --uselogin| docker -east-1  usgion--repassword  get-login-ecraws ken
Get login tobash
# ge:**
```ker Imaocnd Push Duild a``

2. **Bst-1
`s-eaon uegiackend --rerfectshop-bhepry-name tposito-resitory -epor create-rws ec
ash``basitory:**
`CR Repoe Eatre*C
1. *
e**ucturfrastrWS InSetup A*Step 1: 

#### *nded)**te (RecommeFargah AWS ECS wittion A: **Op# 

##enteploym2: AWS Dt 
## ☁️ Par

---
 -f
```unem prteker sys
dochansove-orp--reme down -v osdocker-compg
p everythinClean u
# -build -d
ompose up -
docker-c and start

# Buildrestart apiose r-compkevice
doca ser# Restart ce_name]

-f [servie logs mposr-co logs
docken

# Viewpose dowdocker-comservices
op p -d

# St-compose ukerervices
doc
# Start s

```bashnce**nds Referema**Docker Com### `

``ps
ker-compose rvices
doc all seheck3. C head

# ic upgradei alembexec apompose ocker-cs
dse migrationba 2. Run datad

#d.yml up -se.pro-compo -f dockercomposedocker-mpose file
uction co 1. Use prodash
#
```b
yment** Deplockerion Dop 3: Product
### **Stelth
```
ost:8000/hea//localhhttp:PI
curl  Test the A 6.
#s -f api
-compose logogs
docker. View lse ps

# 5por-comcke status
do. Checkp -d

# 4compose udocker-s
all servicet ar# 3. Stple .env

p .env.exame
c filonment envir2. Copyd

# en
cd backydirectorto backend te  1. Naviga`bash
#

``*nt* Deploymel Dockerep 2: Loca
### **St
```
mposeocker-con/dbial/usr/loco chmod +x /mpose
sudco/docker-/binocal -o /usr/luname -m)" -s)-$(me$(unae-compos0.0/docker-.2/v2ses/downloadreleampose/docker/cogithub.com/ps://tt"hL o curl -
sudr Composecketall Do
# Ins.sh
 get-docker
sudo sh-docker.sh.com -o gett.dockerhttps://gefsSL r
curl -keall DocInstsh
# u):
```bax (Ubunt#### Linu

```ktop
esdocker-dcts/produer.com///www.dockttps:nload from h

# Or dowerockcask dall --w
brew instreg Homeb Usinbash
## Mac:
``````

###rsion
   compose --veocker-on
   der --versiock``cmd
   dn:
   `atioify install Ver
3.ercomputr start yound re a
2. Installker-desktopdocucts/om/proddocker.cttps://www.m hktop froocker Desd D1. Downloa
## Windows:er**

##Install Dock# **Step 1: oyment

##r Depl1: Docke Part 
---

## 🐳sions
e permish appropriatitS Account w
- AWg images)buildin (for cker- Do
onfigured cS CLIyment:
- AWeplo AWS Dor## F

#se
- GitCompo
- Docker inux)er Engine (Lock) or Dacndows/M Desktop (Wi:
- Dockereploymentker D### For Docquisites


## 📋 Prereackend.
ectShop bPerfnt for Theloymeoud depand AWS cltion) oducl/pr(locat  deploymenh Dockers botguide coveris 
Th
WSocker + A Guide: Dymentmplete DeploCo# 🚀 