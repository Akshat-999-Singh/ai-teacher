// The 3D avatar: the Character Creator export in public/avatar.glb, driven with three.js.
// Visemes blend while narration is spoken, the eyes blink on their own clock, and the head
// drifts on the neck bones so she never looks frozen. Nothing here makes a sound: the
// narration is already in the video.
//
// Loaded on demand by AvatarSlot.jsx, so three.js never delays the page.
import * as THREE from 'three'
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'

// Character Creator viseme morph targets on CC_Base_Body.
const VISEMES = ['V_Open', 'V_Explosive', 'V_Dental_Lip', 'V_Tight_O', 'V_Tight', 'V_Wide', 'V_Affricate', 'V_Lip_Open']
const VISEME_EVERY = [0.167, 0.25] // seconds between viseme changes: 4-6 a second
const VISEME_PEAK = [0.4, 0.8] // how far a newly picked viseme is pushed
const MOUTH_RATE = 14 // easing rate, 1/s: a change is 63% done in ~70 ms and never snaps

// Eye_Blink_L/R exists on CC_Base_Body, CC_Base_EyeOcclusion and CC_Base_TearLine. Every
// mesh with the target gets the same value in the same frame; if the occlusion and tear
// line lagged the lids they would float in front of a closed eye.
const BLINKS = ['Eye_Blink_L', 'Eye_Blink_R']
const BLINK_EVERY = [3, 6] // seconds, start to start, whether or not she is speaking
const BLINK_CLOSE = 0.07
const BLINK_HOLD = 0.04
const BLINK_OPEN = 0.12

const SMILES = ['Mouth_Smile_L', 'Mouth_Smile_R']
const SMILE_REST = 0.22 // so she does not look blank between sentences
const SMILE_SPEAKING = 0.12 // eased down a little so it does not fight the visemes
const SMILE_RATE = 4

const FOV = 22

const rand = ([lo, hi]) => lo + Math.random() * (hi - lo)
const approach = (value, target, rate, dt) => value + (target - value) * (1 - Math.exp(-rate * dt))
const smoothstep = (t) => t * t * (3 - 2 * t)

// How closed the eyes are, t seconds after a blink began.
function blinkAmount(t) {
  if (t < 0) return 0
  if (t < BLINK_CLOSE) return smoothstep(t / BLINK_CLOSE)
  if (t < BLINK_CLOSE + BLINK_HOLD) return 1
  const opening = (t - BLINK_CLOSE - BLINK_HOLD) / BLINK_OPEN
  return opening < 1 ? 1 - smoothstep(opening) : 0
}

export function createAvatar(canvas, url, { onReady, onError }) {
  const started = performance.now()
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'low-power' })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.outputColorSpace = THREE.SRGBColorSpace
  renderer.toneMapping = THREE.NeutralToneMapping
  renderer.setClearColor(0x000000, 0)

  const scene = new THREE.Scene()
  const pmrem = new THREE.PMREMGenerator(renderer)
  const environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture
  scene.environment = environment
  scene.environmentIntensity = 0.35
  scene.add(new THREE.HemisphereLight(0xfff1e0, 0x202028, 0.8))
  const key = new THREE.DirectionalLight(0xffe2c6, 2.4)
  key.position.set(1.2, 2.2, 2.4)
  const fill = new THREE.DirectionalLight(0xc8d6ff, 0.6)
  fill.position.set(-1.8, 1.6, 1.2)
  const rim = new THREE.DirectionalLight(0xffffff, 1.2) // separates the hair from the dark ground
  rim.position.set(0, 2.4, -2.5)
  scene.add(key, fill, rim)

  const camera = new THREE.PerspectiveCamera(FOV, 1, 0.05, 20)
  const resize = () => {
    const w = canvas.clientWidth || 1
    const h = canvas.clientHeight || 1
    renderer.setSize(w, h, false)
    camera.aspect = w / h
    camera.updateProjectionMatrix()
  }
  const resizeObserver = new ResizeObserver(resize)
  resizeObserver.observe(canvas)
  resize()

  let disposed = false
  let raf = 0
  let model = null
  let head = null
  let neck = null
  let headRest = null
  let neckRest = null
  const morphs = {} // morph name -> [{ mesh, index, owner }]

  let speaking = false
  const weights = Object.fromEntries(VISEMES.map((v) => [v, 0]))
  const targets = Object.fromEntries(VISEMES.map((v) => [v, 0]))
  let current = null
  let nextVisemeAt = 0
  let smile = SMILE_REST
  let blinkStartedAt = -Infinity
  let nextBlinkAt = performance.now() / 1000 + rand(BLINK_EVERY)
  const idle = !window.matchMedia('(prefers-reduced-motion: reduce)').matches

  const debug = { loadMs: null, frames: 0, maxStep: 0 }

  const setMorph = (name, value) => {
    for (const { mesh, index } of morphs[name] ?? []) mesh.morphTargetInfluences[index] = value
  }

  canvas.addEventListener('webglcontextlost', onContextLost)
  function onContextLost(event) {
    event.preventDefault()
    if (!disposed) onError(new Error('WebGL context lost'))
  }

  new GLTFLoader().load(
    url,
    (gltf) => {
      if (disposed) return disposeModel(gltf.scene)
      try {
        setup(gltf)
      } catch (err) {
        onError(err)
        return
      }
      debug.loadMs = Math.round(performance.now() - started)
      onReady()
      raf = requestAnimationFrame(frame)
    },
    undefined,
    (err) => {
      if (!disposed) onError(err)
    },
  )

  function setup(gltf) {
    model = gltf.scene
    scene.add(model)

    // A multi-primitive glTF mesh becomes a group of meshes; name each by its glTF node.
    const { associations, json } = gltf.parser
    const nodeName = (obj) => {
      const nodes = associations.get(obj)?.nodes
      if (nodes !== undefined) return json.nodes[nodes].name
      return obj.parent ? nodeName(obj.parent) : obj.name
    }
    model.traverse((obj) => {
      if (!obj.isMesh) return
      obj.frustumCulled = false // skinned bounds come from the T-pose, not the lowered arms
      for (const [name, index] of Object.entries(obj.morphTargetDictionary ?? {})) {
        ;(morphs[name] ??= []).push({ mesh: obj, index, owner: nodeName(obj) })
      }
    })
    for (const name of [...VISEMES, ...BLINKS, ...SMILES]) {
      if (!morphs[name]) throw new Error(`avatar.glb has no morph target ${name}`)
    }

    const bone = (name) => {
      const found = model.getObjectByName(name)
      if (!found) throw new Error(`avatar.glb has no bone ${name}`)
      return found
    }
    model.updateMatrixWorld(true)
    const hip = bone('CC_Base_Hip')
    lowerArm(bone('CC_Base_L_Upperarm'), hip)
    lowerArm(bone('CC_Base_R_Upperarm'), hip)

    neck = bone('CC_Base_NeckTwist01')
    head = bone('CC_Base_Head')
    neckRest = neck.quaternion.clone()
    headRest = head.quaternion.clone()

    frameHeadAndShoulders(head, bone('CC_Base_L_Upperarm'), model.getObjectByName('CC_Base_L_Eye'), model.getObjectByName('CC_Base_R_Eye'))
    setMorph('Mouth_Smile_L', smile)
    setMorph('Mouth_Smile_R', smile)
  }

  // The export is a T-pose. Turn each upper arm so shoulder -> elbow points down and a
  // little away from the body. Done in world space, so it needs no knowledge of CC's
  // local bone axes; the forearm and hand follow as children.
  function lowerArm(upperarm, hip) {
    const forearm = upperarm.getObjectByName(upperarm.name.replace('Upperarm', 'Forearm'))
    if (!forearm) throw new Error(`avatar.glb has no forearm under ${upperarm.name}`)
    const shoulder = upperarm.getWorldPosition(new THREE.Vector3())
    const elbow = forearm.getWorldPosition(new THREE.Vector3())
    const side = Math.sign(shoulder.x - hip.getWorldPosition(new THREE.Vector3()).x) || 1
    const now = elbow.sub(shoulder).normalize()
    const wanted = new THREE.Vector3(side * 0.2, -1, 0.05).normalize()
    const turn = new THREE.Quaternion().setFromUnitVectors(now, wanted)
    const world = upperarm.getWorldQuaternion(new THREE.Quaternion())
    const parentWorld = upperarm.parent.getWorldQuaternion(new THREE.Quaternion())
    upperarm.quaternion.copy(parentWorld.invert().multiply(turn.multiply(world)))
    upperarm.updateMatrixWorld(true)
  }

  // Top of the head to just below the shoulders, seen along the face's own forward
  // direction (from the eye bones), so the framing does not assume which way +Z faces.
  function frameHeadAndShoulders(headBone, shoulderBone, eyeL, eyeR) {
    const headAt = headBone.getWorldPosition(new THREE.Vector3())
    const shoulderY = shoulderBone.getWorldPosition(new THREE.Vector3()).y
    const forward = new THREE.Vector3(0, 0, 1)
    if (eyeL && eyeR) {
      const eyes = eyeL.getWorldPosition(new THREE.Vector3()).add(eyeR.getWorldPosition(new THREE.Vector3())).multiplyScalar(0.5)
      const toEyes = eyes.sub(headAt).setY(0)
      if (toEyes.lengthSq() > 1e-8) forward.copy(toEyes.normalize())
    }
    const top = headAt.y + 0.23
    const bottom = shoulderY - 0.1
    const center = new THREE.Vector3(headAt.x, (top + bottom) / 2, headAt.z)
    const distance = (top - bottom) / 2 / Math.tan(THREE.MathUtils.degToRad(FOV / 2))
    camera.position.copy(center).addScaledVector(forward, distance)
    camera.position.y += 0.03
    camera.lookAt(center)
  }

  const euler = new THREE.Euler()
  const tilt = new THREE.Quaternion()

  function update(dt, t) {
    // Visemes: while speaking, pick a new one every 1/6-1/4 s and ease every weight
    // toward its target; the previous viseme's target drops to 0, so they cross-fade.
    if (speaking && t >= nextVisemeAt) {
      let next = current
      while (next === current) next = VISEMES[Math.floor(Math.random() * VISEMES.length)]
      if (current) targets[current] = 0
      targets[next] = rand(VISEME_PEAK)
      current = next
      nextVisemeAt = t + rand(VISEME_EVERY)
    }
    for (const v of VISEMES) {
      const was = weights[v]
      weights[v] = approach(was, targets[v], MOUTH_RATE, dt)
      debug.maxStep = Math.max(debug.maxStep, Math.abs(weights[v] - was))
      setMorph(v, weights[v])
    }

    // Blink on its own clock; every mesh with Eye_Blink_* gets the same value.
    if (t >= nextBlinkAt) {
      blinkStartedAt = t
      nextBlinkAt = t + rand(BLINK_EVERY)
    }
    const lids = blinkAmount(t - blinkStartedAt)
    for (const name of BLINKS) setMorph(name, lids)

    smile = approach(smile, speaking ? SMILE_SPEAKING : SMILE_REST, SMILE_RATE, dt)
    for (const name of SMILES) setMorph(name, smile)

    // Idle head: small, slow, incommensurate sines, so it never visibly loops.
    if (idle) {
      const tau = Math.PI * 2
      const yaw = 0.035 * Math.sin(tau * 0.21 * t) + 0.012 * Math.sin(tau * 0.53 * t + 1.3)
      const pitch = 0.022 * Math.sin(tau * 0.17 * t + 0.6) + 0.008 * Math.sin(tau * 0.41 * t)
      const roll = 0.014 * Math.sin(tau * 0.13 * t + 2.1)
      head.quaternion.copy(headRest).multiply(tilt.setFromEuler(euler.set(pitch, yaw, roll, 'YXZ')))
      neck.quaternion.copy(neckRest).multiply(tilt.setFromEuler(euler.set(pitch * 0.5, yaw * 0.5, roll * 0.5, 'YXZ')))
    }
  }

  let last = performance.now()
  function frame(now) {
    raf = requestAnimationFrame(frame)
    const dt = Math.min((now - last) / 1000, 0.1)
    last = now
    // Nothing to draw while the tab or the Watch view is hidden.
    if (document.hidden || canvas.offsetParent === null) return
    update(dt, now / 1000)
    renderer.render(scene, camera)
    debug.frames++
  }

  function disposeModel(root) {
    root.traverse((obj) => {
      if (!obj.isMesh) return
      obj.geometry.dispose()
      for (const material of [].concat(obj.material)) {
        for (const value of Object.values(material)) if (value?.isTexture) value.dispose()
        material.dispose()
      }
    })
  }

  // Development-only probes for the browser tests (AvatarSlot attaches them in dev).
  Object.assign(debug, {
    speaking: () => speaking,
    visemes: () => ({ ...weights }),
    influence: (owner, name) => {
      const hit = morphs[name]?.find((m) => m.owner === owner)
      return hit ? hit.mesh.morphTargetInfluences[hit.index] : null
    },
    morphNames: () => {
      const byOwner = {}
      for (const [name, list] of Object.entries(morphs)) for (const { owner } of list) (byOwner[owner] ??= new Set()).add(name)
      return Object.fromEntries(Object.entries(byOwner).map(([owner, names]) => [owner, [...names]]))
    },
    headQuaternion: () => head?.quaternion.toArray(),
    armDirections: () =>
      ['CC_Base_L_Upperarm', 'CC_Base_R_Upperarm'].map((name) => {
        const upperarm = model.getObjectByName(name)
        const forearm = model.getObjectByName(name.replace('Upperarm', 'Forearm'))
        return forearm.getWorldPosition(new THREE.Vector3()).sub(upperarm.getWorldPosition(new THREE.Vector3())).normalize().toArray()
      }),
  })

  return {
    debug,
    setSpeaking(on) {
      speaking = on
      if (!on) {
        for (const v of VISEMES) targets[v] = 0 // ease back to rest, never snap
        current = null
      }
    },
    dispose() {
      disposed = true
      cancelAnimationFrame(raf)
      resizeObserver.disconnect()
      canvas.removeEventListener('webglcontextlost', onContextLost)
      if (model) disposeModel(model)
      environment.dispose()
      pmrem.dispose()
      renderer.dispose()
    },
  }
}
